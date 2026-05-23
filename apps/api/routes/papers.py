from __future__ import annotations

import uuid
from pathlib import Path

from fastapi import APIRouter, BackgroundTasks, Depends, File, Form, HTTPException, UploadFile
from fastapi.responses import PlainTextResponse

from api.auth_routes import job_to_list_item
from auth.service import assert_job_owner, get_current_user
from schema.models import JobListItem, JobRecord, JobStatus
from storage.jobs import UPLOADS, job_store, now_iso
from storage.users import User
from worker.tasks import process_paper_job, process_pdf_job

router = APIRouter(prefix="/v1/papers", tags=["papers"])


async def _enqueue_or_run(coro_factory, *args) -> None:
    try:
        from arq import create_pool
        from arq.connections import RedisSettings
        import os

        redis_url = os.getenv("REDIS_URL", "redis://localhost:6379")
        host = redis_url.split("://")[-1].split(":")[0]
        port = int(redis_url.split(":")[-1] or 6379)
        redis = await create_pool(RedisSettings(host=host, port=port))
        await redis.enqueue_job(coro_factory.__name__, *args)
    except Exception:
        await coro_factory({}, *args)


@router.get("", response_model=list[JobListItem])
async def list_papers(user: User = Depends(get_current_user)):
    records = job_store.list_by_user(user.id)
    return [job_to_list_item(r) for r in records]


@router.post("", status_code=202)
async def upload_paper(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    mineru_file: UploadFile | None = File(None),
    journal_profile: str = Form("scut_natural_science"),
    user: User = Depends(get_current_user),
):
    job_id = str(uuid.uuid4())
    job_dir = UPLOADS / job_id
    job_dir.mkdir(parents=True, exist_ok=True)

    filename = file.filename or "upload"
    dest = job_dir / filename
    content = await file.read()
    dest.write_bytes(content)

    record = JobRecord(
        job_id=job_id,
        status=JobStatus.QUEUED,
        journal_profile=journal_profile,
        user_id=user.id,
        filename=filename,
        created_at=now_iso(),
        updated_at=now_iso(),
    )
    job_store.save(record)

    if filename.lower().endswith(".pdf"):
        background_tasks.add_task(_enqueue_or_run, process_pdf_job, job_id, str(dest), journal_profile)
    else:
        mineru_path = None
        if mineru_file and mineru_file.filename:
            mineru_dest = job_dir / mineru_file.filename
            mineru_dest.write_bytes(await mineru_file.read())
            mineru_path = str(mineru_dest)
        background_tasks.add_task(
            _enqueue_or_run,
            process_paper_job,
            job_id,
            str(dest),
            mineru_path,
            journal_profile,
        )

    return {"job_id": job_id, "status": JobStatus.QUEUED}


@router.get("/{job_id}")
async def get_job(job_id: str, user: User = Depends(get_current_user)):
    record = job_store.get(job_id)
    if not record:
        raise HTTPException(404, "job not found")
    assert_job_owner(record, user)
    return {
        "job_id": record.job_id,
        "status": record.status,
        "journal_profile": record.journal_profile,
        "filename": record.filename,
        "error": record.error,
        "updated_at": record.updated_at,
        "created_at": record.created_at,
    }


@router.get("/{job_id}/report")
async def get_report(job_id: str, user: User = Depends(get_current_user)):
    record = job_store.get(job_id)
    if not record:
        raise HTTPException(404, "job not found")
    assert_job_owner(record, user)
    if record.status != JobStatus.DONE or not record.report:
        raise HTTPException(409, f"report not ready, status={record.status}")
    return record.report.model_dump(mode="json")


@router.get("/{job_id}/report.md", response_class=PlainTextResponse)
async def get_report_md(job_id: str, user: User = Depends(get_current_user)):
    from orchestrator.runner import report_to_markdown

    record = job_store.get(job_id)
    if not record:
        raise HTTPException(404, "job not found")
    assert_job_owner(record, user)
    if not record.report:
        raise HTTPException(404, "report not found")
    return report_to_markdown(record.report)
