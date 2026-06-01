from __future__ import annotations

import os
from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_DB = ROOT / "data" / "mse.db"

_engine = None
_SessionLocal = None
_bound_url: str | None = None


def _database_url() -> str:
    return os.getenv("MSE_DATABASE_URL", f"sqlite:///{DEFAULT_DB}")


def _ensure_engine() -> None:
    global _engine, _SessionLocal, _bound_url
    url = _database_url()
    if _engine is not None and _bound_url == url:
        return
    connect_args = {"check_same_thread": False} if url.startswith("sqlite") else {}
    _engine = create_engine(url, connect_args=connect_args)
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
    if url.startswith("sqlite:///"):
        path_str = url.replace("sqlite:///", "", 1)
        db_path = Path(path_str) if path_str.startswith("/") else ROOT / path_str
        db_path.parent.mkdir(parents=True, exist_ok=True)

    _ensure_engine()
    assert _engine is not None
    Base.metadata.create_all(bind=_engine)


def reset_engine() -> None:
    """Test helper: force engine rebind on next get_session()."""
    global _engine, _SessionLocal, _bound_url
    if _engine is not None:
        _engine.dispose()
    _engine = None
    _SessionLocal = None
    _bound_url = None
