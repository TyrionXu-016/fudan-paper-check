from __future__ import annotations

import asyncio
import os
from pathlib import Path
from urllib.parse import urlparse

from parser.fusion import DualSourceFusionParser
from parser.span_builder import build_spans
from orchestrator.issue_enricher import enrich_issues
from orchestrator.runner import report_to_markdown
from orchestrator.agent_runner import AgentRunner
from orchestrator.progress import notify as progress_notify
from schema.models import DetectStage, JobRecord, JobStatus
from storage.jobs import STORAGE, UPLOADS, job_store, now_iso
from rag.doc_index import build_task_index, drop_task_index


def _set_progress(
    record: JobRecord,
    *,
    stage: DetectStage,
    percent: int,
    message: str,
    status: JobStatus | None = None,
) -> None:
    record.current_stage = stage
    record.progress_percent = percent
    record.progress_message = message
    if status is not None:
        record.status = status
    record.updated_at = now_iso()
    job_store.save(record)
    progress_notify(record.job_id, stage, percent, message)


async def process_paper_job(
    ctx: dict,
    job_id: str,
    maker_path: str,
    mineru_path: str | None,
    journal_profile: str,
) -> dict:
    record = job_store.get(job_id)
    if not record:
        record = JobRecord(job_id=job_id, status=JobStatus.QUEUED, created_at=now_iso())
    _set_progress(
        record,
        stage=DetectStage.PARSING,
        percent=10,
        message="正在解析文档",
        status=JobStatus.PARSING,
    )

    try:
        parser = DualSourceFusionParser()
        doc = parser.parse_files(maker_path, mineru_path)
        spans = build_spans(doc)
        record.document = doc
        record.spans = spans
        job_store.save(record)

        # Build RAG-2 index
        build_task_index(job_id, doc, spans)

        _set_progress(
            record,
            stage=DetectStage.FORMAT_CHECK,
            percent=40,
            message="正在执行检查",
            status=JobStatus.CHECKING,
        )

        runner = AgentRunner(journal_profile=journal_profile)

        def _on_progress(stage: DetectStage, percent: int, message: str) -> None:
            _set_progress(
                record,
                stage=stage,
                percent=percent,
                message=message,
                status=JobStatus.CHECKING,
            )

        report = runner.run(doc, spans, job_id, on_progress=_on_progress)
        report.issues = enrich_issues(report.issues, doc, spans)

        _set_progress(
            record,
            stage=DetectStage.DONE,
            percent=100,
            message=f"检测完成，共发现 {len(report.issues)} 项问题",
            status=JobStatus.DONE,
        )
        record.report = report
        record.updated_at = now_iso()
        job_store.save(record)
        
        # Cleanup RAG-2 index
        drop_task_index(job_id)

        md_path = STORAGE / f"{job_id}.report.md"
        md_path.write_text(report_to_markdown(report), encoding="utf-8")
        return {"job_id": job_id, "status": "done"}
    except Exception as exc:
        record.status = JobStatus.FAILED
        record.error = str(exc)
        record.current_stage = DetectStage.ERROR
        record.progress_message = str(exc)
        record.updated_at = now_iso()
        job_store.save(record)
        raise


async def process_pdf_job(
    ctx: dict,
    job_id: str,
    pdf_path: str,
    journal_profile: str,
) -> dict:
    from worker.converter import PDFConverter

    record = job_store.get(job_id)
    if not record:
        record = JobRecord(job_id=job_id, status=JobStatus.QUEUED, created_at=now_iso())
    _set_progress(
        record,
        stage=DetectStage.PARSING,
        percent=5,
        message="正在转换 PDF",
        status=JobStatus.CONVERTING,
    )

    out_dir = UPLOADS / job_id
    out_dir.mkdir(parents=True, exist_ok=True)
    converter = PDFConverter()
    maker_path, mineru_path = await asyncio.to_thread(
        converter.convert, Path(pdf_path), out_dir
    )
    return await process_paper_job(
        ctx,
        job_id,
        str(maker_path),
        str(mineru_path) if mineru_path else None,
        journal_profile,
    )


def _build_redis_settings():
    from arq.connections import RedisSettings

    redis_url = os.getenv("REDIS_URL", "redis://localhost:6379")
    parsed = urlparse(redis_url)
    return RedisSettings(
        host=parsed.hostname or "localhost",
        port=parsed.port or 6379,
        database=int((parsed.path or "/0").lstrip("/") or "0"),
        username=parsed.username,
        password=parsed.password,
        ssl=parsed.scheme == "rediss",
    )


class WorkerSettings:
    functions = [process_paper_job, process_pdf_job]
    redis_settings = _build_redis_settings()
    job_timeout = 600
