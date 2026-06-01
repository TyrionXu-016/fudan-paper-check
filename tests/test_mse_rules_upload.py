from __future__ import annotations

import uuid

import pytest
from fastapi.testclient import TestClient

from api.main import app
from rag.mse_rule_index import load_project_index, project_sources_dir
from storage.db import init_db, reset_engine


@pytest.fixture(autouse=True)
def _db(tmp_path, monkeypatch):
    reset_engine()
    db_path = tmp_path / "mse.db"
    monkeypatch.setenv("MSE_DATABASE_URL", f"sqlite:///{db_path}")
    monkeypatch.setenv("MSE_ALLOW_MOCK_FALLBACK", "1")
    users_path = tmp_path / "users.json"
    monkeypatch.setenv("USERS_JSON", str(users_path))
    monkeypatch.setattr("storage.users.USERS_FILE", users_path)
    init_db()
    yield
    reset_engine()


def _register(client: TestClient, role: str) -> tuple[str, str]:
    email = f"{role}-{uuid.uuid4().hex[:8]}@test.local"
    res = client.post(
        "/v1/auth/register",
        json={"email": email, "password": "secret123", "name": role, "role": role},
    )
    assert res.status_code == 200
    return res.json()["access_token"], email


def test_upload_rule_markdown_increases_index(tmp_path):
    client = TestClient(app)
    adv_token, _ = _register(client, "advisor")
    headers = {"Authorization": f"Bearer {adv_token}"}

    res = client.post(
        "/v1/mse/projects",
        json={"title": "规范测试", "student_email": "stu@test.local"},
        headers=headers,
    )
    project_id = res.json()["id"]

    spec = tmp_path / "spec.md"
    spec.write_text("# 摘要\n\n摘要应包含关键词。\n\n# 参考文献\n\n引用格式要求。\n", encoding="utf-8")

    with spec.open("rb") as fh:
        up = client.post(
            f"/v1/mse/projects/{project_id}/rules",
            headers=headers,
            files={"file": ("spec.md", fh, "text/markdown")},
        )
    assert up.status_code == 200
    body = up.json()
    assert body["rule_base_ids"]

    index = load_project_index(project_id)
    assert index is not None
    assert index["chunk_count"] >= 2
    assert (project_sources_dir(project_id) / f"{body['rule_base_ids'][-1]}.md").exists()


def test_upload_rule_rejects_empty_md(tmp_path):
    client = TestClient(app)
    adv_token, _ = _register(client, "advisor")
    headers = {"Authorization": f"Bearer {adv_token}"}
    res = client.post(
        "/v1/mse/projects",
        json={"title": "空规范", "student_email": "stu@test.local"},
        headers=headers,
    )
    project_id = res.json()["id"]
    empty = tmp_path / "empty.md"
    empty.write_text("   \n", encoding="utf-8")
    with empty.open("rb") as fh:
        up = client.post(
            f"/v1/mse/projects/{project_id}/rules",
            headers=headers,
            files={"file": ("empty.md", fh, "text/markdown")},
        )
    assert up.status_code == 400
