from __future__ import annotations

from fastapi import APIRouter, BackgroundTasks, Depends, File, Form, HTTPException, UploadFile

from api.auth_routes import job_to_list_item
from api.services.upload import PAPERS_ALLOWED_SUFFIXES, create_check_job
from auth.service import assert_job_owner, get_current_user
from schema.models import JobListItem, JobStatus
from storage.jobs import job_store
from storage.users import User

router = APIRouter(prefix="/v1/papers", tags=["papers"])


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
    record = await create_check_job(
        background_tasks,
        user_id=user.id,
        file=file,
        rule_base_id=journal_profile,
        mineru_file=mineru_file,
        allowed_suffixes=PAPERS_ALLOWED_SUFFIXES,
    )
    return {"job_id": record.job_id, "status": JobStatus.QUEUED}


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
        "current_stage": record.current_stage,
        "progress_percent": record.progress_percent,
        "progress_message": record.progress_message,
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


@router.get("/{job_id}/report.md")
async def get_report_md(job_id: str, user: User = Depends(get_current_user)):
    from fastapi.responses import PlainTextResponse
    from orchestrator.runner import report_to_markdown

    record = job_store.get(job_id)
    if not record:
        raise HTTPException(404, "job not found")
    assert_job_owner(record, user)
    if not record.report:
        raise HTTPException(404, "report not found")
    return PlainTextResponse(report_to_markdown(record.report))
