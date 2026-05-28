from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, Depends
from fastapi.responses import FileResponse

from auth.service import assert_job_owner, get_current_user
from orchestrator.export_doc import write_export_file
from orchestrator.preview import build_preview
from schema.api_response import (
    ERROR_TASK_NOT_FOUND,
    ERROR_TASK_NOT_READY,
    ERROR_UNSUPPORTED_FORMAT,
    ApiError,
    ApiResponse,
)
from schema.models import ExportRequest, ExportResponse, JobStatus
from storage.decisions import load_decisions, upsert_decisions
from storage.jobs import STORAGE, job_store
from storage.users import User

router = APIRouter(prefix="/v1/tasks", tags=["export"])

EXPORTS_DIR = STORAGE / "exports"
SUPPORTED_FORMATS = {"docx", "md", "pdf"}


def _assert_task_ready(record) -> None:
    if record.status != JobStatus.DONE or not record.report:
        raise ApiError(
            ERROR_TASK_NOT_READY,
            f"task not ready for export, status={record.status.value}",
            status_code=409,
        )


def _resolve_decisions(task_id: str, incoming) -> dict:
    if incoming:
        return upsert_decisions(task_id, incoming)
    return load_decisions(task_id)


def _export_path(task_id: str, fmt: str) -> Path:
    return EXPORTS_DIR / f"{task_id}.{fmt}"


@router.post("/{task_id}/export")
async def create_export(
    task_id: str,
    body: ExportRequest,
    user: User = Depends(get_current_user),
) -> ApiResponse[ExportResponse]:
    record = job_store.get(task_id)
    if not record:
        raise ApiError(ERROR_TASK_NOT_FOUND, "task not found", status_code=404)
    assert_job_owner(record, user)
    _assert_task_ready(record)

    fmt = body.format.lower()
    if fmt not in SUPPORTED_FORMATS:
        raise ApiError(
            ERROR_UNSUPPORTED_FORMAT,
            f"unsupported export format: {fmt}",
            status_code=400,
            detail=f"allowed: {', '.join(sorted(SUPPORTED_FORMATS))}",
        )

    decisions = _resolve_decisions(task_id, body.decisions)
    preview = build_preview(record, decisions)
    dest = _export_path(task_id, fmt)
    write_export_file(preview, fmt, dest)

    return ApiResponse.success(
        ExportResponse(
            unresolved_count=preview.unresolved_count,
            filename=dest.name,
            format=fmt,
        )
    )


@router.get("/{task_id}/export/{fmt}")
async def download_export(
    task_id: str,
    fmt: str,
    user: User = Depends(get_current_user),
):
    record = job_store.get(task_id)
    if not record:
        raise ApiError(ERROR_TASK_NOT_FOUND, "task not found", status_code=404)
    assert_job_owner(record, user)
    _assert_task_ready(record)

    fmt = fmt.lower()
    if fmt not in SUPPORTED_FORMATS:
        raise ApiError(
            ERROR_UNSUPPORTED_FORMAT,
            f"unsupported export format: {fmt}",
            status_code=400,
        )

    dest = _export_path(task_id, fmt)
    if not dest.exists():
        decisions = load_decisions(task_id)
        preview = build_preview(record, decisions)
        write_export_file(preview, fmt, dest)

    media_types = {
        "docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        "md": "text/markdown; charset=utf-8",
        "pdf": "application/pdf",
    }
    return FileResponse(
        dest,
        media_type=media_types.get(fmt, "application/octet-stream"),
        filename=dest.name,
    )
