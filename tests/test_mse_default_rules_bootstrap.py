from __future__ import annotations

import uuid

import pytest
from fastapi.testclient import TestClient

from api.main import app
from rag.mse_rule_index import load_project_index
from rag.mse_rule_retriever import retrieve_project_rules
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


def _register(client: TestClient, role: str) -> str:
    email = f"{role}-{uuid.uuid4().hex[:8]}@test.local"
    res = client.post(
        "/v1/auth/register",
        json={"email": email, "password": "secret123", "name": role, "role": role},
    )
    assert res.status_code == 200
    return res.json()["access_token"]


def test_create_project_bootstraps_default_rules():
    client = TestClient(app)
    adv_token = _register(client, "advisor")
    headers = {"Authorization": f"Bearer {adv_token}"}

    res = client.post(
        "/v1/mse/projects",
        json={"title": "默认规范", "student_email": "stu@test.local"},
        headers=headers,
    )
    assert res.status_code == 200
    body = res.json()
    project_id = body["id"]
    assert body["rule_base_ids"]

    index = load_project_index(project_id)
    assert index is not None
    assert index["chunk_count"] >= 15
    sources = {c.get("source", "") for c in index.get("chunks") or []}
    assert any("thesis_common_problems.md" in s for s in sources)


def test_retrieve_hits_thesis_faq_on_references():
    client = TestClient(app)
    adv_token = _register(client, "advisor")
    headers = {"Authorization": f"Bearer {adv_token}"}
    res = client.post(
        "/v1/mse/projects",
        json={"title": "检索测试", "student_email": "stu2@test.local"},
        headers=headers,
    )
    project_id = res.json()["id"]
    hits = retrieve_project_rules(project_id, "参考文献", top_k=5)
    assert hits.results
    assert any("参考" in r.text for r in hits.results)
