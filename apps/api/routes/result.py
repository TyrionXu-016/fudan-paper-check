from __future__ import annotations

from fastapi import APIRouter, Depends

from auth.service import assert_job_owner, get_current_user
from schema.api_response import ERROR_TASK_NOT_FOUND, ERROR_TASK_NOT_READY, ApiError, ApiResponse
from schema.models import CheckReport, DocumentView, JobStatus
from storage.jobs import job_store
from storage.users import User

router = APIRouter(prefix="/v1/result", tags=["result"])


@router.get("/{task_id}")
async def get_result(
    task_id: str,
    user: User = Depends(get_current_user),
) -> ApiResponse[CheckReport]:
    record = job_store.get(task_id)
    if not record:
        raise ApiError(ERROR_TASK_NOT_FOUND, "task not found", status_code=404)
    assert_job_owner(record, user)
    if record.status != JobStatus.DONE or not record.report:
        raise ApiError(
            ERROR_TASK_NOT_READY,
            f"result not ready, status={record.status.value}",
            status_code=409,
            detail=record.error,
        )
    return ApiResponse.success(record.report)


@router.get("/{task_id}/document")
async def get_document(
    task_id: str,
    user: User = Depends(get_current_user),
) -> ApiResponse[DocumentView]:
    record = job_store.get(task_id)
    if not record:
        raise ApiError(ERROR_TASK_NOT_FOUND, "task not found", status_code=404)
    assert_job_owner(record, user)
    if record.status != JobStatus.DONE or not record.document:
        raise ApiError(
            ERROR_TASK_NOT_READY,
            f"document not ready, status={record.status.value}",
            status_code=409,
            detail=record.error,
        )
    doc = record.document
    title = record.report.paper_title if record.report else doc.meta.title
    return ApiResponse.success(
        DocumentView(
            sections=doc.sections,
            spans=record.spans,
            paper_title=title,
        )
    )
