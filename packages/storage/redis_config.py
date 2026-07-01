from __future__ import annotations

import os


def get_redis_url(default: str = "redis://localhost:6379") -> str:
    return os.getenv("REDIS_URL", default).strip() or default


def build_arq_redis_settings():
    from arq.connections import RedisSettings

    return RedisSettings.from_dsn(get_redis_url())
