from __future__ import annotations

from fastapi import APIRouter, BackgroundTasks, Depends, Form

from api.services.upload import restart_check_job
from auth.service import assert_job_owner, get_current_user
from schema.api_response import ERROR_TASK_NOT_FOUND, ApiError, ApiResponse
from schema.models import CheckSubmitResponse, JobStatus, TaskStatusView
from storage.jobs import job_store
from storage.users import User

router = APIRouter(prefix="/v1/tasks", tags=["tasks"])


def _to_task_view(record) -> TaskStatusView:
    return TaskStatusView(
        task_id=record.job_id,
        status=record.status,
        rule_base_id=record.journal_profile,
        filename=record.filename,
        error=record.error,
        current_stage=record.current_stage,
        progress_percent=record.progress_percent,
        progress_message=record.progress_message,
        created_at=record.created_at,
        updated_at=record.updated_at,
    )


@router.get("/{task_id}")
async def get_task(
    task_id: str,
    user: User = Depends(get_current_user),
) -> ApiResponse[TaskStatusView]:
    record = job_store.get(task_id)
    if not record:
        raise ApiError(ERROR_TASK_NOT_FOUND, "task not found", status_code=404)
    assert_job_owner(record, user)
    return ApiResponse.success(_to_task_view(record))


@router.post("/{task_id}/restart", status_code=202)
async def restart_task(
    task_id: str,
    background_tasks: BackgroundTasks,
    rule_base_id: str = Form("generic"),
    user: User = Depends(get_current_user),
) -> ApiResponse[CheckSubmitResponse]:
    record = job_store.get(task_id)
    if not record:
        raise ApiError(ERROR_TASK_NOT_FOUND, "task not found", status_code=404)
    assert_job_owner(record, user)
    record = await restart_check_job(
        background_tasks,
        task_id=task_id,
        rule_base_id=rule_base_id,
    )
    return ApiResponse.success(
        CheckSubmitResponse(task_id=record.job_id, status=JobStatus.QUEUED)
    )
