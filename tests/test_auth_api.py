import uuid

import pytest
from fastapi.testclient import TestClient

from api.main import app

client = TestClient(app)


@pytest.fixture
def auth_headers():
    email = f"user_{uuid.uuid4().hex[:8]}@example.com"
    res = client.post(
        "/v1/auth/register",
        json={"email": email, "password": "secret12", "name": "Tester"},
    )
    assert res.status_code == 200
    token = res.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def test_register_and_login():
    email = f"login_{uuid.uuid4().hex[:8]}@example.com"
    reg = client.post(
        "/v1/auth/register",
        json={"email": email, "password": "secret12", "name": "Demo"},
    )
    assert reg.status_code == 200
    login = client.post(
        "/v1/auth/login",
        json={"email": email, "password": "secret12"},
    )
    assert login.status_code == 200
    assert login.json()["access_token"]


def test_list_jobs_requires_auth():
    res = client.get("/v1/papers")
    assert res.status_code == 401


def test_upload_and_list_jobs(auth_headers, tmp_path):
    maker = tmp_path / "sample.md"
    maker.write_text("# 标题\n\n摘 要: 测试摘要内容。\n\n### 参考文献:\n\n- [1] 作者. 题名 [J]. 期刊, 2024.\n", encoding="utf-8")

    with maker.open("rb") as f:
        upload = client.post(
            "/v1/papers",
            headers=auth_headers,
            files={"file": ("sample.md", f, "text/markdown")},
            data={"journal_profile": "generic"},
    )
    assert upload.status_code == 202
    job_id = upload.json()["data"]["job_id"]

    listed = client.get("/v1/papers", headers=auth_headers)
    assert listed.status_code == 200
    body = listed.json()
    assert body["code"] == 0
    ids = [item["job_id"] for item in body["data"]]
    assert job_id in ids

    detail = client.get(f"/v1/papers/{job_id}", headers=auth_headers)
    assert detail.status_code == 200
    assert detail.json()["data"]["job_id"] == job_id
