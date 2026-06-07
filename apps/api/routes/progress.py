from __future__ import annotations

import asyncio
from typing import AsyncIterator

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse

from auth.service import assert_job_owner, get_current_user
from orchestrator.progress import format_sse, iter_redis_events, subscribe, unsubscribe
from schema.api_response import ERROR_TASK_NOT_FOUND, ApiError, ApiResponse
from schema.models import DetectStage, JobStatus, ProgressEvent
from storage.jobs import job_store
from storage.users import User

router = APIRouter(prefix="/v1/detect/progress", tags=["progress"])


def _current_event(record) -> dict:
    stage = record.current_stage or DetectStage.UPLOADING
    return ProgressEvent(
        stage=stage,
        percent=record.progress_percent,
        message=record.progress_message or "",
    ).model_dump(mode="json")


@router.get("/{task_id}")
async def stream_progress(
    task_id: str,
    user: User = Depends(get_current_user),
):
    record = job_store.get(task_id)
    if not record:
        raise ApiError(ERROR_TASK_NOT_FOUND, "task not found", status_code=404)
    assert_job_owner(record, user)

    async def event_generator() -> AsyncIterator[str]:
        queue: asyncio.Queue = asyncio.Queue()
        subscribe(task_id, queue)
        redis_task = asyncio.create_task(_forward_redis(task_id, queue))
        last_key = None
        try:
            while True:
                record = job_store.get(task_id)
                if not record:
                    break

                payload = _current_event(record)
                key = (payload["stage"], payload["percent"], payload["message"])
                if key != last_key:
                    yield format_sse("progress", payload)
                    last_key = key

                if record.status in {JobStatus.DONE, JobStatus.FAILED}:
                    event_name = "done" if record.status == JobStatus.DONE else "error"
                    yield format_sse(event_name, payload)
                    break

                try:
                    queued = queue.get_nowait()
                    payload = queued
                    key = (payload["stage"], payload["percent"], payload["message"])
                    if key != last_key:
                        yield format_sse("progress", payload)
                        last_key = key
                except asyncio.QueueEmpty:
                    pass

                await asyncio.sleep(0.25)
        finally:
            redis_task.cancel()
            unsubscribe(task_id, queue)

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


async def _forward_redis(task_id: str, queue: asyncio.Queue) -> None:
    import os

    if not os.getenv("REDIS_URL", "").strip():
        return
    try:
        async for payload in iter_redis_events(task_id):
            await queue.put(payload)
    except asyncio.CancelledError:
        raise
    except Exception:
        return
