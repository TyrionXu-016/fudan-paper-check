from __future__ import annotations

import asyncio
import os
from pathlib import Path

from parser.fusion import DualSourceFusionParser
from orchestrator.runner import CheckOrchestrator, report_to_markdown
from schema.models import JobRecord, JobStatus
from storage.jobs import STORAGE, UPLOADS, job_store, now_iso


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
    record.status = JobStatus.PARSING
    record.updated_at = now_iso()
    job_store.save(record)

    try:
        parser = DualSourceFusionParser()
        doc = parser.parse_files(maker_path, mineru_path)

        record.status = JobStatus.CHECKING
        record.updated_at = now_iso()
        job_store.save(record)

        orchestrator = CheckOrchestrator(journal_profile=journal_profile)
        report = orchestrator.run(doc, job_id)

        record.status = JobStatus.DONE
        record.report = report
        record.updated_at = now_iso()
        job_store.save(record)

        md_path = STORAGE / f"{job_id}.report.md"
        md_path.write_text(report_to_markdown(report), encoding="utf-8")
        return {"job_id": job_id, "status": "done"}
    except Exception as exc:
        record.status = JobStatus.FAILED
        record.error = str(exc)
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
    record.status = JobStatus.CONVERTING
    record.updated_at = now_iso()
    job_store.save(record)

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


class WorkerSettings:
    functions = [process_paper_job, process_pdf_job]
    redis_settings = os.getenv("REDIS_URL", "redis://localhost:6379")
    job_timeout = 600
