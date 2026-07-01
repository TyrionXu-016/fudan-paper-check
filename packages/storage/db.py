from __future__ import annotations

import os
from threading import Lock
from pathlib import Path

from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session, sessionmaker

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_DB = ROOT / "data" / "mse.db"

_engine = None
_SessionLocal = None
_bound_url: str | None = None
_initialized_key: tuple[str, str | None] | None = None
_init_lock = Lock()


def _database_url() -> str:
    url = os.getenv("MSE_DATABASE_URL")
    if not url:
        raise RuntimeError("MSE_DATABASE_URL is required; use Supabase Postgres for runtime deployments")
    return _normalize_database_url(url)


def _normalize_database_url(url: str) -> str:
    if url.startswith("postgres://"):
        return "postgresql+psycopg://" + url.removeprefix("postgres://")
    if url.startswith("postgresql://"):
        return "postgresql+psycopg://" + url.removeprefix("postgresql://")
    return url


def _is_postgres_url(url: str) -> bool:
    return url.startswith("postgresql")


def _db_schema() -> str | None:
    return os.getenv("MSE_DB_SCHEMA") or None


def _ensure_engine() -> None:
    global _engine, _SessionLocal, _bound_url
    url = _database_url()
    if _engine is not None and _bound_url == url:
        return
    connect_args = {"check_same_thread": False} if url.startswith("sqlite") else {}
    engine_kwargs = {"pool_pre_ping": True} if _is_postgres_url(url) else {}
    _engine = create_engine(url, connect_args=connect_args, **engine_kwargs)
    _SessionLocal = sessionmaker(bind=_engine, autocommit=False, autoflush=False)
    _bound_url = url


def get_engine():
    _ensure_engine()
    return _engine


def get_session() -> Session:
    _ensure_engine()
    assert _SessionLocal is not None
    return _SessionLocal()


def init_db() -> None:
    from storage.models_orm import Base

    url = _database_url()
    schema = _db_schema()
    init_key = (url, schema)

    global _initialized_key
    if _initialized_key == init_key:
        return

    with _init_lock:
        if _initialized_key == init_key:
            return

        if url.startswith("sqlite:///"):
            path_str = url.replace("sqlite:///", "", 1)
            db_path = Path(path_str) if path_str.startswith("/") else ROOT / path_str
            db_path.parent.mkdir(parents=True, exist_ok=True)

        _ensure_engine()
        assert _engine is not None
        if _is_postgres_url(url) and schema:
            with _engine.begin() as conn:
                conn.execute(text(f'CREATE SCHEMA IF NOT EXISTS "{schema}"'))
        Base.metadata.create_all(bind=_engine)
        if _is_postgres_url(url) and os.getenv("MSE_ENABLE_RLS", "1") != "0":
            with _engine.begin() as conn:
                for table in Base.metadata.sorted_tables:
                    schema_prefix = f'"{table.schema}".' if table.schema else ""
                    conn.execute(text(f'ALTER TABLE {schema_prefix}"{table.name}" ENABLE ROW LEVEL SECURITY'))
        _initialized_key = init_key


def reset_engine() -> None:
    """Test helper: force engine rebind on next get_session()."""
    global _engine, _SessionLocal, _bound_url, _initialized_key
    if _engine is not None:
        _engine.dispose()
    _engine = None
    _SessionLocal = None
    _bound_url = None
    _initialized_key = None
