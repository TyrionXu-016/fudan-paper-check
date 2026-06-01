from __future__ import annotations

import os
import uuid
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

os.environ["JOB_RUN_INLINE"] = "1"

from api.main import app
from storage.db import init_db, reset_engine


@pytest.fixture(autouse=True)
def _db(tmp_path, monkeypatch):
    reset_engine()
    db_path = tmp_path / "mse.db"
    monkeypatch.setenv("MSE_DATABASE_URL", f"sqlite:///{db_path}")
    monkeypatch.setenv("MSE_ALLOW_MOCK_FALLBACK", "1")
    users_path = tmp_path / "users.json"
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


def test_invite_get_and_accept_by_token():
    client = TestClient(app)
    adv_token, _ = _register(client, "advisor")
    stu_token, stu_email = _register(client, "student")
    headers = {"Authorization": f"Bearer {adv_token}"}

    res = client.post(
        "/v1/mse/projects",
        json={"title": "邀请测试", "student_email": stu_email},
        headers=headers,
    )
    project_id = res.json()["id"]
    inv = client.post(f"/v1/mse/projects/{project_id}/invite", headers=headers).json()
    token = inv["token"]

    info = client.get(f"/v1/mse/invites/{token}").json()
    assert info["project_title"] == "邀请测试"
    assert info["target_role"] == "student"
    assert not info["used"]

    stu_headers = {"Authorization": f"Bearer {stu_token}"}
    accepted = client.post(f"/v1/mse/invites/{token}/accept", headers=stu_headers)
    assert accepted.status_code == 200
    assert accepted.json()["student_id"]

    info2 = client.get(f"/v1/mse/invites/{token}").json()
    assert info2["used"]


def test_invite_submit_without_auth(tmp_path):
    client = TestClient(app)
    adv_token, _ = _register(client, "advisor")
    headers = {"Authorization": f"Bearer {adv_token}"}

    stu_email = f"invite-stu-{uuid.uuid4().hex[:8]}@test.local"
    res = client.post(
        "/v1/mse/projects",
        json={"title": "免登录提交", "student_email": stu_email},
        headers=headers,
    )
    project_id = res.json()["id"]
    client.post(f"/v1/mse/projects/{project_id}/rules/default", headers=headers)

    inv = client.post(f"/v1/mse/projects/{project_id}/invite", headers=headers).json()
    token = inv["token"]

    samples = Path(__file__).resolve().parents[1] / "samples"
    maker = next(samples.glob("*_maker.md"), None)
    assert maker, "need sample md"
    with maker.open("rb") as fh:
        sub = client.post(
            f"/v1/mse/invites/{token}/submissions",
            files={"file": ("paper.pdf", fh, "application/pdf")},
        )
    assert sub.status_code == 200
    assert sub.json()["round_number"] == 1

    project = client.get(f"/v1/mse/projects/{project_id}", headers=headers).json()
    assert project["student_id"]

    info = client.get(f"/v1/mse/invites/{token}").json()
    assert info["used"]

    with maker.open("rb") as fh:
        again = client.post(
            f"/v1/mse/invites/{token}/submissions",
            files={"file": ("paper.pdf", fh, "application/pdf")},
        )
    assert again.status_code == 400
