from __future__ import annotations

import uuid
import shutil
from pathlib import Path

from fastapi import APIRouter, BackgroundTasks, Depends, File, Form, UploadFile
from pydantic import BaseModel, Field

from api.services.upload import (
    CHECK_ALLOWED_SUFFIXES,
    MAX_UPLOAD_BYTES,
    create_check_job,
    create_check_job_from_bytes,
    validate_rule_base,
)
from auth.service import get_current_user
from schema.api_response import ERROR_FILE_TOO_LARGE, ERROR_TASK_NOT_FOUND, ApiError, ApiResponse
from schema.models import CheckSubmitResponse, JobStatus
from storage.jobs import UPLOADS
from storage.users import User

router = APIRouter(prefix="/v1", tags=["check"])

CHUNK_ROOT = UPLOADS / "chunks"


class ChunkInitRequest(BaseModel):
    filename: str
    size: int = Field(ge=1)
    chunks: int = Field(ge=1)
    rule_base_id: str = "generic"


class ChunkInitResponse(BaseModel):
    upload_id: str


class ChunkCompleteRequest(BaseModel):
    upload_id: str


class ChunkMeta(BaseModel):
    user_id: str
    filename: str
    size: int
    chunks: int
    rule_base_id: str


def _chunk_dir(upload_id: str) -> Path:
    return CHUNK_ROOT / upload_id


def _meta_path(upload_id: str) -> Path:
    return _chunk_dir(upload_id) / "meta.json"


def _load_meta(upload_id: str, user: User) -> ChunkMeta:
    path = _meta_path(upload_id)
    if not path.exists():
        raise ApiError(ERROR_TASK_NOT_FOUND, "chunk upload not found", status_code=404)
    meta = ChunkMeta.model_validate_json(path.read_text(encoding="utf-8"))
    if meta.user_id != user.id:
        raise ApiError("FORBIDDEN", "forbidden", status_code=403)
    return meta


@router.post("/check", status_code=202)
async def submit_check(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    rule_base_id: str = Form("generic"),
    user: User = Depends(get_current_user),
) -> ApiResponse[CheckSubmitResponse]:
    record = await create_check_job(
        background_tasks,
        user_id=user.id,
        file=file,
        rule_base_id=rule_base_id,
        allowed_suffixes=CHECK_ALLOWED_SUFFIXES,
    )
    return ApiResponse.success(
        CheckSubmitResponse(task_id=record.job_id, status=JobStatus.QUEUED)
    )


@router.post("/check/chunks/init")
async def init_chunk_upload(
    body: ChunkInitRequest,
    user: User = Depends(get_current_user),
) -> ApiResponse[ChunkInitResponse]:
    validate_rule_base(body.rule_base_id)
    if body.size > MAX_UPLOAD_BYTES:
        raise ApiError(
            ERROR_FILE_TOO_LARGE,
            f"file exceeds {MAX_UPLOAD_BYTES // (1024 * 1024)}MB limit",
            status_code=413,
        )

    upload_id = str(uuid.uuid4())
    folder = _chunk_dir(upload_id)
    folder.mkdir(parents=True, exist_ok=True)
    meta = ChunkMeta(
        user_id=user.id,
        filename=body.filename,
        size=body.size,
        chunks=body.chunks,
        rule_base_id=body.rule_base_id,
    )
    _meta_path(upload_id).write_text(meta.model_dump_json(indent=2), encoding="utf-8")
    return ApiResponse.success(ChunkInitResponse(upload_id=upload_id))


@router.post("/check/chunks/upload")
async def upload_chunk(
    upload_id: str = Form(...),
    index: int = Form(...),
    total: int = Form(...),
    chunk: UploadFile = File(...),
    user: User = Depends(get_current_user),
) -> ApiResponse[dict]:
    meta = _load_meta(upload_id, user)
    if total != meta.chunks or index < 0 or index >= meta.chunks:
        raise ApiError("INVALID_CHUNK", "invalid chunk index", status_code=400)

    content = await chunk.read()
    folder = _chunk_dir(upload_id)
    (folder / f"{index}.part").write_bytes(content)
    return ApiResponse.success({})


@router.post("/check/chunks/complete", status_code=202)
async def complete_chunk_upload(
    body: ChunkCompleteRequest,
    background_tasks: BackgroundTasks,
    user: User = Depends(get_current_user),
) -> ApiResponse[CheckSubmitResponse]:
    meta = _load_meta(body.upload_id, user)
    folder = _chunk_dir(body.upload_id)
    parts = [folder / f"{idx}.part" for idx in range(meta.chunks)]
    missing = [idx for idx, path in enumerate(parts) if not path.exists()]
    if missing:
        raise ApiError("MISSING_CHUNK", f"missing chunks: {missing}", status_code=400)

    content = b"".join(path.read_bytes() for path in parts)
    if len(content) != meta.size:
        raise ApiError("INVALID_CHUNK_UPLOAD", "assembled file size mismatch", status_code=400)

    record = await create_check_job_from_bytes(
        background_tasks,
        user_id=user.id,
        filename=meta.filename,
        content=content,
        rule_base_id=meta.rule_base_id,
        allowed_suffixes=CHECK_ALLOWED_SUFFIXES,
    )
    shutil.rmtree(folder, ignore_errors=True)
    return ApiResponse.success(
        CheckSubmitResponse(task_id=record.job_id, status=JobStatus.QUEUED)
    )
