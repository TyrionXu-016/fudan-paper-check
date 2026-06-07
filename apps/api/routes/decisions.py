from __future__ import annotations

from fastapi import APIRouter, Depends

from auth.service import assert_job_owner, get_current_user
from orchestrator.preview import build_preview
from schema.api_response import ERROR_TASK_NOT_FOUND, ERROR_TASK_NOT_READY, ApiError, ApiResponse
from schema.models import Decision, DecisionsPayload, JobStatus, PreviewView
from storage.decisions import load_decisions, patch_decision, upsert_decisions
from storage.jobs import job_store
from storage.users import User

router = APIRouter(prefix="/v1/tasks", tags=["decisions"])


def _assert_task_ready(record) -> None:
    if record.status != JobStatus.DONE or not record.report:
        raise ApiError(
            ERROR_TASK_NOT_READY,
            f"task not ready for decisions, status={record.status.value}",
            status_code=409,
        )


@router.get("/{task_id}/decisions")
async def get_decisions(
    task_id: str,
    user: User = Depends(get_current_user),
) -> ApiResponse[list[Decision]]:
    record = job_store.get(task_id)
    if not record:
        raise ApiError(ERROR_TASK_NOT_FOUND, "task not found", status_code=404)
    assert_job_owner(record, user)
    _assert_task_ready(record)
    decisions = load_decisions(task_id)
    return ApiResponse.success(list(decisions.values()))


@router.put("/{task_id}/decisions")
async def put_decisions(
    task_id: str,
    body: DecisionsPayload,
    user: User = Depends(get_current_user),
) -> ApiResponse[list[Decision]]:
    record = job_store.get(task_id)
    if not record:
        raise ApiError(ERROR_TASK_NOT_FOUND, "task not found", status_code=404)
    assert_job_owner(record, user)
    _assert_task_ready(record)
    saved = upsert_decisions(task_id, body.decisions)
    return ApiResponse.success(list(saved.values()))


@router.patch("/{task_id}/decisions/{issue_id}")
async def patch_issue_decision(
    task_id: str,
    issue_id: str,
    body: Decision,
    user: User = Depends(get_current_user),
) -> ApiResponse[Decision]:
    record = job_store.get(task_id)
    if not record:
        raise ApiError(ERROR_TASK_NOT_FOUND, "task not found", status_code=404)
    assert_job_owner(record, user)
    _assert_task_ready(record)
    saved = patch_decision(task_id, issue_id, body)
    return ApiResponse.success(saved)


@router.get("/{task_id}/preview")
async def get_preview(
    task_id: str,
    user: User = Depends(get_current_user),
) -> ApiResponse[PreviewView]:
    record = job_store.get(task_id)
    if not record:
        raise ApiError(ERROR_TASK_NOT_FOUND, "task not found", status_code=404)
    assert_job_owner(record, user)
    _assert_task_ready(record)
    decisions = load_decisions(task_id)
    preview = build_preview(record, decisions)
    return ApiResponse.success(preview)
