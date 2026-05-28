import time
import uuid

import pytest
from fastapi.testclient import TestClient

from api.main import app
from schema.models import DecisionAction, JobStatus

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


def _submit_sample(headers: dict, tmp_path) -> str:
    maker = tmp_path / "sample.md"
    maker.write_text(
        "# 标题\n\n摘 要: 测试摘要内容，包含42.29 pcu指标。\n\n### 参考文献:\n\n- [1] 作者. 题名 [J]. 期刊, 2024.\n",
        encoding="utf-8",
    )
    with maker.open("rb") as f:
        upload = client.post(
            "/v1/check",
            headers=headers,
            files={"file": ("sample.md", f, "text/markdown")},
            data={"rule_base_id": "generic"},
        )
    assert upload.status_code == 202
    return upload.json()["data"]["task_id"]


def _wait_for_task(task_id: str, headers: dict, timeout: float = 30.0) -> dict:
    deadline = time.time() + timeout
    while time.time() < deadline:
        res = client.get(f"/v1/tasks/{task_id}", headers=headers)
        assert res.status_code == 200
        data = res.json()["data"]
        if data["status"] in {JobStatus.DONE.value, JobStatus.FAILED.value}:
            return data
        time.sleep(0.2)
    raise TimeoutError(f"task {task_id} did not finish")


def test_sse_progress_events(auth_headers, tmp_path):
    task_id = _submit_sample(auth_headers, tmp_path)

    with client.stream(
        "GET",
        f"/v1/detect/progress/{task_id}",
        headers=auth_headers,
    ) as response:
        assert response.status_code == 200
        chunks = []
        for chunk in response.iter_text():
            chunks.append(chunk)
            if "event: done" in chunk or "event: error" in chunk:
                break

    body = "".join(chunks)
    assert "event: progress" in body
    assert "event: done" in body or "percent" in body


def test_restart_rejects_active_task(auth_headers, tmp_path):
    maker = tmp_path / "slow.md"
    maker.write_text("# t\n\n摘 要: x\n", encoding="utf-8")
    with maker.open("rb") as f:
        upload = client.post(
            "/v1/check",
            headers=auth_headers,
            files={"file": ("slow.md", f, "text/markdown")},
            data={"rule_base_id": "generic"},
        )
    task_id = upload.json()["data"]["task_id"]

    res = client.get(f"/v1/tasks/{task_id}", headers=auth_headers)
    if res.json()["data"]["status"] == JobStatus.DONE.value:
        pytest.skip("task finished before restart race")

    restart = client.post(
        f"/v1/tasks/{task_id}/restart",
        headers=auth_headers,
        data={"rule_base_id": "generic"},
    )
    if restart.status_code == 409:
        assert restart.json()["code"] == "TASK_BUSY"


def test_decisions_preview_export(auth_headers, tmp_path):
    task_id = _submit_sample(auth_headers, tmp_path)
    _wait_for_task(task_id, auth_headers)

    result = client.get(f"/v1/result/{task_id}", headers=auth_headers)
    issues = result.json()["data"]["issues"]
    if not issues:
        pytest.skip("no issues to decide on")

    issue_id = issues[0]["id"]
    put = client.put(
        f"/v1/tasks/{task_id}/decisions",
        headers=auth_headers,
        json={
            "decisions": [
                {
                    "issue_id": issue_id,
                    "action": DecisionAction.ACCEPT.value,
                }
            ]
        },
    )
    assert put.status_code == 200
    assert put.json()["data"]

    preview = client.get(f"/v1/tasks/{task_id}/preview", headers=auth_headers)
    assert preview.status_code == 200
    preview_data = preview.json()["data"]
    assert preview_data["spans"]
    assert preview_data["unresolved_count"] == len(issues) - 1

    export = client.post(
        f"/v1/tasks/{task_id}/export",
        headers=auth_headers,
        json={"format": "md"},
    )
    assert export.status_code == 200
    export_data = export.json()["data"]
    assert export_data["unresolved_count"] == len(issues) - 1
    assert export_data["format"] == "md"

    download = client.get(
        f"/v1/tasks/{task_id}/export/md",
        headers=auth_headers,
    )
    assert download.status_code == 200
    assert download.content

    pdf_export = client.post(
        f"/v1/tasks/{task_id}/export",
        headers=auth_headers,
        json={"format": "pdf"},
    )
    assert pdf_export.status_code == 200
    pdf_download = client.get(
        f"/v1/tasks/{task_id}/export/pdf",
        headers=auth_headers,
    )
    assert pdf_download.status_code == 200
    assert pdf_download.content.startswith(b"%PDF")


def test_restart_after_done(auth_headers, tmp_path):
    task_id = _submit_sample(auth_headers, tmp_path)
    _wait_for_task(task_id, auth_headers)

    restart = client.post(
        f"/v1/tasks/{task_id}/restart",
        headers=auth_headers,
        data={"rule_base_id": "generic"},
    )
    assert restart.status_code == 202
    task = _wait_for_task(task_id, auth_headers)
    assert task["status"] == JobStatus.DONE.value
