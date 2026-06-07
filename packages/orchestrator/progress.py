from __future__ import annotations

import json
import os
from typing import Callable

from schema.models import DetectStage, ProgressEvent

ProgressCallback = Callable[[DetectStage, int, str], None]

# 进程内 SSE 订阅队列（API 与 inline worker 同进程时即时推送）
_subscribers: dict[str, list] = {}


def _redis_client():
    url = os.getenv("REDIS_URL", "").strip()
    if not url:
        return None
    try:
        import redis

        return redis.from_url(url)
    except Exception:
        return None


def subscribe(task_id: str, queue) -> None:
    _subscribers.setdefault(task_id, []).append(queue)


def unsubscribe(task_id: str, queue) -> None:
    queues = _subscribers.get(task_id, [])
    if queue in queues:
        queues.remove(queue)
    if not queues:
        _subscribers.pop(task_id, None)


def _publish_redis(task_id: str, data: dict) -> None:
    client = _redis_client()
    if client is None:
        return
    try:
        client.publish(f"progress:{task_id}", json.dumps(data, ensure_ascii=False))
    except Exception:
        pass


def notify(task_id: str, stage: DetectStage, percent: int, message: str) -> None:
    payload = ProgressEvent(stage=stage, percent=percent, message=message)
    data = payload.model_dump(mode="json")
    for queue in list(_subscribers.get(task_id, [])):
        try:
            queue.put_nowait(data)
        except Exception:
            pass
    _publish_redis(task_id, data)


def format_sse(event: str, data: dict) -> str:
    return f"event: {event}\ndata: {json.dumps(data, ensure_ascii=False)}\n\n"


async def iter_redis_events(task_id: str):
    url = os.getenv("REDIS_URL", "").strip()
    if not url:
        return
    try:
        from redis.asyncio import from_url as redis_from_url
    except Exception:
        return

    client = redis_from_url(url)
    pubsub = client.pubsub()
    await pubsub.subscribe(f"progress:{task_id}")
    try:
        async for message in pubsub.listen():
            if message.get("type") != "message":
                continue
            raw = message.get("data")
            if isinstance(raw, bytes):
                raw = raw.decode("utf-8")
            yield json.loads(raw)
    finally:
        await pubsub.unsubscribe(f"progress:{task_id}")
        await pubsub.close()
        await client.close()

