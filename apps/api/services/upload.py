from __future__ import annotations

import os
import uuid
from pathlib import Path

from fastapi import BackgroundTasks, UploadFile

from schema.api_response import (
    ERROR_FILE_TOO_LARGE,
    ERROR_RULE_BASE_NOT_FOUND,
    ERROR_TASK_NOT_FOUND,
    ERROR_UNSUPPORTED_FORMAT,
    ApiError,
)
from orchestrator.fsm import assert_can_restart
from schema.models import DetectStage, JobRecord, JobStatus
from rule_bases.service import get_rule_base
from storage.decisions import clear_decisions
from storage.jobs import UPLOADS, job_store, now_iso
from worker.tasks import process_paper_job, process_pdf_job

MAX_UPLOAD_BYTES = 50 * 1024 * 1024

CHECK_ALLOWED_SUFFIXES = {".pdf", ".docx", ".md", ".markdown"}
PAPERS_ALLOWED_SUFFIXES = {".pdf", ".md", ".markdown"}


async def _enqueue_or_run(coro_factory, *args) -> None:
    if os.getenv("JOB_RUN_INLINE", "").lower() in ("1", "true", "yes"):
        await coro_factory({}, *args)
        return
    try:
        from arq import create_pool
        from arq.connections import RedisSettings

        redis_url = os.getenv("REDIS_URL", "redis://localhost:6379")
        host = redis_url.split("://")[-1].split(":")[0]
        port = int(redis_url.split(":")[-1] or 6379)
        redis = await create_pool(RedisSettings(host=host, port=port))
        await redis.enqueue_job(coro_factory.__name__, *args)
    except Exception:
        await coro_factory({}, *args)


def _suffix(filename: str) -> str:
    return Path(filename or "upload").suffix.lower()


def validate_upload_file(
    filename: str,
    content: bytes,
    *,
    allowed_suffixes: set[str],
) -> None:
    suffix = _suffix(filename)
    if suffix not in allowed_suffixes:
        raise ApiError(
            ERROR_UNSUPPORTED_FORMAT,
            f"unsupported file format: {suffix or '(none)'}",
            status_code=400,
            detail=f"allowed: {', '.join(sorted(allowed_suffixes))}",
        )
    if len(content) > MAX_UPLOAD_BYTES:
        raise ApiError(
            ERROR_FILE_TOO_LARGE,
            f"file exceeds {MAX_UPLOAD_BYTES // (1024 * 1024)}MB limit",
            status_code=413,
        )


def validate_rule_base(rule_base_id: str) -> str:
    if get_rule_base(rule_base_id) is None:
        raise ApiError(
            ERROR_RULE_BASE_NOT_FOUND,
            f"rule base not found: {rule_base_id}",
            status_code=404,
        )
    return rule_base_id


async def create_check_job(
    background_tasks: BackgroundTasks,
    *,
    user_id: str,
    file: UploadFile,
    rule_base_id: str = "generic",
    mineru_file: UploadFile | None = None,
    allowed_suffixes: set[str] | None = None,
) -> JobRecord:
    allowed = allowed_suffixes or CHECK_ALLOWED_SUFFIXES
    filename = file.filename or "upload"
    content = await file.read()
    return await create_check_job_from_bytes(
        background_tasks,
        user_id=user_id,
        filename=filename,
        content=content,
        rule_base_id=rule_base_id,
        mineru_file=mineru_file,
        allowed_suffixes=allowed,
    )


async def create_check_job_from_bytes(
    background_tasks: BackgroundTasks,
    *,
    user_id: str,
    filename: str,
    content: bytes,
    rule_base_id: str = "generic",
    mineru_file: UploadFile | None = None,
    allowed_suffixes: set[str] | None = None,
) -> JobRecord:
    allowed = allowed_suffixes or CHECK_ALLOWED_SUFFIXES
    validate_rule_base(rule_base_id)
    validate_upload_file(filename, content, allowed_suffixes=allowed)

    job_id = str(uuid.uuid4())
    job_dir = UPLOADS / job_id
    job_dir.mkdir(parents=True, exist_ok=True)

    dest = job_dir / filename
    dest.write_bytes(content)

    record = JobRecord(
        job_id=job_id,
        status=JobStatus.QUEUED,
        journal_profile=rule_base_id,
        user_id=user_id,
        filename=filename,
        current_stage=DetectStage.UPLOADING,
        progress_percent=0,
        progress_message="等待处理",
        created_at=now_iso(),
        updated_at=now_iso(),
    )
    job_store.save(record)

    suffix = _suffix(filename)
    if suffix == ".pdf":
        background_tasks.add_task(
            _enqueue_or_run, process_pdf_job, job_id, str(dest), rule_base_id
        )
    else:
        mineru_path = None
        if mineru_file and mineru_file.filename:
            mineru_content = await mineru_file.read()
            validate_upload_file(
                mineru_file.filename,
                mineru_content,
                allowed_suffixes={".md", ".markdown"},
            )
            mineru_dest = job_dir / mineru_file.filename
            mineru_dest.write_bytes(mineru_content)
            mineru_path = str(mineru_dest)
        background_tasks.add_task(
            _enqueue_or_run,
            process_paper_job,
            job_id,
            str(dest),
            mineru_path,
            rule_base_id,
        )

    return record


def _pick_source_file(job_dir: Path, record: JobRecord) -> Path:
    if record.filename:
        candidate = job_dir / record.filename
        if candidate.exists():
            return candidate
    files = [p for p in job_dir.iterdir() if p.is_file()]
    if not files:
        raise ApiError(
            ERROR_UNSUPPORTED_FORMAT,
            "no source file found for restart",
            status_code=400,
        )
    return sorted(files, key=lambda p: p.stat().st_mtime)[0]


async def restart_check_job(
    background_tasks: BackgroundTasks,
    *,
    task_id: str,
    rule_base_id: str = "generic",
) -> JobRecord:
    record = job_store.get(task_id)
    if not record:
        raise ApiError(ERROR_TASK_NOT_FOUND, "task not found", status_code=404)

    assert_can_restart(record)
    validate_rule_base(rule_base_id)

    job_dir = UPLOADS / task_id
    if not job_dir.exists():
        raise ApiError(
            ERROR_UNSUPPORTED_FORMAT,
            "original upload files not found for restart",
            status_code=400,
        )

    source = _pick_source_file(job_dir, record)

    clear_decisions(task_id)
    record.status = JobStatus.QUEUED
    record.journal_profile = rule_base_id
    record.error = None
    record.report = None
    record.document = None
    record.spans = []
    record.current_stage = DetectStage.UPLOADING
    record.progress_percent = 0
    record.progress_message = "等待重新检测"
    record.updated_at = now_iso()
    job_store.save(record)

    suffix = source.suffix.lower()
    if suffix == ".pdf":
        background_tasks.add_task(
            _enqueue_or_run, process_pdf_job, task_id, str(source), rule_base_id
        )
    else:
        mineru_candidates = [
            p
            for p in job_dir.iterdir()
            if p.suffix.lower() in {".md", ".markdown"} and p != source
        ]
        mineru_path = str(mineru_candidates[0]) if mineru_candidates else None
        background_tasks.add_task(
            _enqueue_or_run,
            process_paper_job,
            task_id,
            str(source),
            mineru_path,
            rule_base_id,
        )

    return record
