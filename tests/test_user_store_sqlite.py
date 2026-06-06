from __future__ import annotations

import json
import uuid

from fastapi.testclient import TestClient

from api.main import app
from storage.db import get_session, init_db, reset_engine
from storage.models_orm import UserORM
from storage.users import user_store


def test_user_store_migrates_legacy_json_to_sqlite_once(tmp_path, monkeypatch):
    db_path = tmp_path / "mse.db"
    users_file = tmp_path / "users.json"
    user_id = str(uuid.uuid4())
    users_file.write_text(
        json.dumps(
            {
                user_id: {
                    "id": user_id,
                    "email": "legacy@example.com",
                    "name": "Legacy",
                    "password_hash": "salt$digest",
                    "created_at": "2026-01-01T00:00:00+00:00",
                }
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setenv("MSE_DATABASE_URL", f"sqlite:///{db_path}")
    monkeypatch.setattr("storage.users.USERS_FILE", users_file)
    reset_engine()
    init_db()

    imported = user_store.migrate_json_once()
    imported_again = user_store.migrate_json_once()

    assert imported == 1
    assert imported_again == 0
    assert user_store.get(user_id).email == "legacy@example.com"
    assert user_store.get_by_email("LEGACY@example.com").role == "advisor"
    assert len(list(tmp_path.glob("users.json.bak-*"))) == 1

    session = get_session()
    try:
        rows = session.query(UserORM).filter(UserORM.email == "legacy@example.com").all()
        assert len(rows) == 1
    finally:
        session.close()


def test_auth_register_writes_sqlite_without_recreating_users_json(tmp_path, monkeypatch):
    db_path = tmp_path / "mse.db"
    users_file = tmp_path / "users.json"
    monkeypatch.setenv("MSE_DATABASE_URL", f"sqlite:///{db_path}")
    monkeypatch.setattr("storage.users.USERS_FILE", users_file)
    reset_engine()
    init_db()

    client = TestClient(app)
    email = f"sqlite-{uuid.uuid4().hex[:8]}@example.com"
    res = client.post(
        "/v1/auth/register",
        json={"email": email, "password": "secret12", "name": "SQLite", "role": "student"},
    )

    assert res.status_code == 200, res.text
    assert res.json()["user"]["role"] == "student"
    assert not users_file.exists()

    session = get_session()
    try:
        row = session.query(UserORM).filter(UserORM.email == email).one()
        assert row.name == "SQLite"
        assert row.role == "student"
    finally:
        session.close()
