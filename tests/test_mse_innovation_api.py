"""Innovation review API integration."""

from __future__ import annotations

import uuid

import pytest
from fastapi.testclient import TestClient

from api.main import app
from mse.innovation import build_innovation_review
from parser.fusion import DualSourceFusionParser
from storage.db import init_db, reset_engine
from storage.jobs import UPLOADS, job_store, now_iso
from storage.mse_repository import MseRepository
from storage.users import user_store
from schema.models import JobRecord, JobStatus


@pytest.fixture(autouse=True)
def _db(tmp_path, monkeypatch):
    reset_engine()
    db_path = tmp_path / "mse.db"
    monkeypatch.setenv("MSE_DATABASE_URL", f"sqlite:///{db_path}")
    users_path = tmp_path / "users.json"
    monkeypatch.setenv("USERS_JSON", str(users_path))
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


def test_innovation_review_submit():
    client = TestClient(app)
    adv_token, stu_email = _register(client, "advisor")
    stu_token, _ = _register(client, "student")
    headers = {"Authorization": f"Bearer {adv_token}"}

    res = client.post(
        "/v1/mse/projects",
        json={"title": "创新测试", "student_email": stu_email},
        headers=headers,
    )
    project_id = res.json()["id"]
    client.post(f"/v1/mse/projects/{project_id}/rules/default", headers=headers)

    from auth.mse import get_repo

    repo = get_repo()
    repo.bind_member(project_id, student_id=user_store.get_by_email(stu_email).id)

    parser = DualSourceFusionParser()
    maker = "samples/基于集成深度学习模型的公路隧道交通流预测_钱超_maker.md"
    doc = parser.parse_files(maker, None)
    job_id = str(uuid.uuid4())
    out = UPLOADS / job_id
    out.mkdir(parents=True, exist_ok=True)
    job_store.save(
        JobRecord(
            job_id=job_id,
            status=JobStatus.DONE,
            filename="paper_maker.md",
            journal_profile="generic",
            created_at=now_iso(),
            updated_at=now_iso(),
            document=doc,
        )
    )
    round_obj = repo.create_round(project_id, job_id)
    round_obj.gate_passed = True
    round_obj.review_status = __import__("mse.models", fromlist=["ReviewStatus"]).ReviewStatus.PASSED
    from mse.models import ProjectStatus

    project = repo.get_project(project_id)
    project.status = ProjectStatus.AWAITING_ADVISOR
    repo.save_project(project)
    repo.update_round(round_obj)

    preview = build_innovation_review(project_id, round_obj.id, doc)
    repo.save_innovation_review(preview)

    get_res = client.get(f"/v1/mse/projects/{project_id}/innovation-review", headers=headers)
    assert get_res.status_code == 200
    assert get_res.json()["llm_summary"]

    post_res = client.post(
        f"/v1/mse/projects/{project_id}/innovation-review",
        json={"advisor_comment": "创新点明确", "advisor_decision": "approve"},
        headers=headers,
    )
    assert post_res.status_code == 200
    body = post_res.json()
    assert body["advisor_decision"] == "approve"
    assert repo.get_project(project_id).status.value == "completed"
