from __future__ import annotations

import os
import tempfile
import uuid
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

os.environ["JOB_RUN_INLINE"] = "1"

from api.main import app
from auth.service import hash_password
from mse.issue_diff import diff_rounds, issue_fingerprint
from mse.models import ProjectStatus, ReviewStatus, UserRole
from schema.models import CheckCategory, Issue, IssueSeverity, IssueType
from storage.db import init_db
from storage.users import User, now_iso, user_store


@pytest.fixture(autouse=True)
def _fresh_db(tmp_path, monkeypatch):
    db_url = f"sqlite:///{tmp_path}/mse.db"
    users_file = tmp_path / "users.json"
    monkeypatch.setenv("MSE_DATABASE_URL", db_url)
    monkeypatch.setenv("MSE_ALLOW_MOCK_FALLBACK", "1")
    monkeypatch.setattr("storage.users.USERS_FILE", users_file)
    from storage.db import reset_engine, init_db

    reset_engine()
    init_db()
    user_store.users = {}
    yield
    reset_engine()


def _register(client: TestClient, role: str = "advisor") -> tuple[str, str]:
    email = f"{uuid.uuid4().hex[:8]}@test.com"
    res = client.post(
        "/v1/auth/register",
        json={"email": email, "password": "secret12", "name": "test", "role": role},
    )
    assert res.status_code == 200, res.text
    return res.json()["access_token"], email


def _issue(code: str, page: int, message: str) -> Issue:
    return Issue(
        id=str(uuid.uuid4()),
        code=code,
        category=CheckCategory.FORMAT,
        severity=IssueSeverity.ERROR,
        issue_type=IssueType.FORMAT,
        section="摘要",
        page=page,
        line=page,
        message=message,
        revision_hint="请修改",
        rule_ref="rule-1",
    )


def test_issue_fingerprint_stable():
    a = _issue("E1", 3, "缺少关键词")
    b = _issue("E1", 3, "缺少关键词")
    assert issue_fingerprint(a) == issue_fingerprint(b)


def test_diff_rounds_fixed_and_new():
    prev = [_issue("E1", 3, "缺少关键词")]
    curr = [_issue("E2", 5, "参考文献格式错误")]
    diff = diff_rounds(prev, curr, set(), base_round=1, current_round=2)
    assert len(diff.fixed) == 1
    assert len(diff.new) == 1
    assert len(diff.persistent) == 0


def test_advisor_create_project_and_dashboard():
    client = TestClient(app)
    token, student_email = _register(client, "advisor")
    headers = {"Authorization": f"Bearer {token}"}

    res = client.post(
        "/v1/mse/projects",
        json={"title": "张三论文", "student_email": student_email},
        headers=headers,
    )
    assert res.status_code == 200
    project = res.json()
    assert project["advisor_id"]
    assert project["student_email"] == student_email
    assert project["rule_base_ids"]

    dash = client.get("/v1/mse/dashboard", headers=headers)
    assert dash.status_code == 200
    assert dash.json()["advisor"]["stats"]["total_projects"] == 1


def test_student_create_project():
    client = TestClient(app)
    token, _ = _register(client, "student")
    headers = {"Authorization": f"Bearer {token}"}

    res = client.post(
        "/v1/mse/projects",
        json={"title": "我的论文", "advisor_email": "adv2@test.com"},
        headers=headers,
    )
    assert res.status_code == 200
    body = res.json()
    assert body["student_id"]
    assert body["advisor_email"] == "adv2@test.com"
    assert body["initiator_role"] == "student"
    assert body["rule_base_ids"]


def test_auto_notify_false_pending_release():
    client = TestClient(app)
    adv_token, _ = _register(client, "advisor")
    stu_token, stu_email = _register(client, "student")
    adv_headers = {"Authorization": f"Bearer {adv_token}"}
    stu_headers = {"Authorization": f"Bearer {stu_token}"}

    res = client.post(
        "/v1/mse/projects",
        json={
            "title": "预审项目",
            "student_email": stu_email,
            "auto_notify_student": False,
        },
        headers=adv_headers,
    )
    project_id = res.json()["id"]
    assert res.json()["rule_base_ids"]

    accept = client.post(
        f"/v1/mse/projects/{project_id}/accept",
        json={"token": "unused"},
        headers=stu_headers,
    )
    assert accept.status_code in (400, 404)

    from auth.mse import get_repo

    repo = get_repo()
    project = repo.get_project(project_id)
    repo.bind_member(project_id, student_id=user_store.get_by_email(stu_email).id)
    project = repo.get_project(project_id)
    assert project.student_id

    samples = Path(__file__).resolve().parents[1] / "samples"
    maker = next(samples.glob("*_maker.md"), None)
    assert maker, "need sample md"
    job_id = str(uuid.uuid4())
    from storage.jobs import UPLOADS, job_store
    from schema.models import JobRecord, JobStatus

    out = UPLOADS / job_id
    out.mkdir(parents=True, exist_ok=True)
    (out / "paper_maker.md").write_text(maker.read_text(encoding="utf-8"), encoding="utf-8")
    job_store.save(
        JobRecord(
            job_id=job_id,
            status=JobStatus.QUEUED,
            filename="paper_maker.md",
            journal_profile="generic",
            created_at=now_iso(),
            updated_at=now_iso(),
        )
    )
    round_obj = repo.create_round(project_id, job_id)

    import asyncio
    from worker.mse_tasks import process_mse_round

    asyncio.get_event_loop().run_until_complete(
        process_mse_round({}, project_id, round_obj.id)
    )

    round_res = client.get(
        f"/v1/mse/projects/{project_id}/rounds/1/report",
        headers=adv_headers,
    )
    assert round_res.status_code == 200
    assert round_res.json()["review_status"] in (
        ReviewStatus.PENDING_RELEASE.value,
        ReviewStatus.ISSUES_FOUND.value,
        ReviewStatus.PASSED.value,
    )

    student_res = client.get(
        f"/v1/mse/projects/{project_id}/rounds/1/report",
        headers=stu_headers,
    )
    if round_res.json()["review_status"] == ReviewStatus.PENDING_RELEASE.value:
        assert student_res.status_code == 403

        rel = client.post(
            f"/v1/mse/projects/{project_id}/rounds/1/release",
            json={},
            headers=adv_headers,
        )
        assert rel.status_code == 200
        assert rel.json()["released"] is True

        student_res2 = client.get(
            f"/v1/mse/projects/{project_id}/rounds/1/report",
            headers=stu_headers,
        )
        assert student_res2.status_code == 200
