from __future__ import annotations

import api.env_loader  # noqa: F401 — load .env before worker reads env

import asyncio
import os
from pathlib import Path

from parser.fusion import DualSourceFusionParser
from parser.span_builder import build_spans
from orchestrator.issue_enricher import enrich_issues
from orchestrator.runner import CheckOrchestrator, report_to_markdown
from orchestrator.progress import notify as progress_notify
from schema.models import DetectStage, JobRecord, JobStatus
from storage.jobs import STORAGE, UPLOADS, job_store, now_iso


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

        _set_progress(
            record,
            stage=DetectStage.FORMAT_CHECK,
            percent=40,
            message="正在执行检查",
            status=JobStatus.CHECKING,
        )

        orchestrator = CheckOrchestrator(journal_profile=journal_profile)

        def _on_progress(stage: DetectStage, percent: int, message: str) -> None:
            _set_progress(
                record,
                stage=stage,
                percent=percent,
                message=message,
                status=JobStatus.CHECKING,
            )

        report = orchestrator.run(doc, job_id, on_progress=_on_progress)
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
    host_port = redis_url.split("://")[-1]
    host = host_port.split(":")[0]
    port = int(host_port.split(":")[-1] if ":" in host_port else 6379)
    return RedisSettings(host=host, port=port)


from worker.mse_tasks import process_mse_round, retry_mse_round_parse


class WorkerSettings:
    functions = [
        process_paper_job,
        process_pdf_job,
        process_mse_round,
        retry_mse_round_parse,
    ]
    redis_settings = _build_redis_settings()
    job_timeout = 600
