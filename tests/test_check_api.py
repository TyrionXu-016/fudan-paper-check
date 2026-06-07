import time
import uuid

import pytest
from fastapi.testclient import TestClient

from api.main import app
from schema.models import JobStatus

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


def test_rule_bases_list():
    res = client.get("/v1/rule_bases")
    assert res.status_code == 200
    body = res.json()
    assert body["code"] == 0
    assert body["message"] == "ok"
    ids = {item["id"] for item in body["data"]}
    assert "generic" in ids
    assert "fudan_university" in ids
    assert "fudan_thesis" in ids
    assert "scut_natural_science" in ids


def test_rule_bases_detail():
    res = client.get("/v1/rule_bases/generic")
    assert res.status_code == 200
    data = res.json()["data"]
    assert data["display_name"]
    assert data["summary"]["format"]


def test_fudan_rule_base_detail():
    res = client.get("/v1/rule_bases/fudan_university")
    assert res.status_code == 200
    data = res.json()["data"]
    assert data["display_name"] == "复旦大学论文规范"
    assert "abstract" in data["required_sections"]
    assert "references" in data["required_sections"]


def test_fudan_thesis_rule_base_detail():
    res = client.get("/v1/rule_bases/fudan_thesis")
    assert res.status_code == 200
    data = res.json()["data"]
    assert data["id"] == "fudan_thesis"
    assert data["display_name"] == "复旦大学博士、硕士学位论文规范"
    assert "中文摘要" in data["required_sections"]
    assert "论文独创性声明与使用授权声明" in data["required_sections"]
    assert "正文宋体、小四号" in data["summary"]["format"]


def test_rule_bases_not_found():
    res = client.get("/v1/rule_bases/does-not-exist")
    assert res.status_code == 404
    assert res.json()["code"] == "RULE_BASE_NOT_FOUND"


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


def test_check_upload_and_result(auth_headers, tmp_path):
    maker = tmp_path / "sample.md"
    maker.write_text(
        "# 标题\n\n摘 要: 测试摘要内容，包含42.29 pcu指标。\n\n### 参考文献:\n\n- [1] 作者. 题名 [J]. 期刊, 2024.\n",
        encoding="utf-8",
    )

    with maker.open("rb") as f:
        upload = client.post(
            "/v1/check",
            headers=auth_headers,
            files={"file": ("sample.md", f, "text/markdown")},
            data={"rule_base_id": "generic"},
        )
    assert upload.status_code == 202
    body = upload.json()
    assert body["code"] == 0
    task_id = body["data"]["task_id"]

    task = _wait_for_task(task_id, auth_headers)
    assert task["status"] == JobStatus.DONE.value
    assert task["progress_percent"] == 100

    result = client.get(f"/v1/result/{task_id}", headers=auth_headers)
    assert result.status_code == 200
    report = result.json()["data"]
    assert report["job_id"] == task_id
    assert report["summary"]["errors"] + report["summary"]["warnings"] >= 0
    if report["issues"]:
        issue = report["issues"][0]
        assert issue["id"]
        assert issue["issue_type"]

    doc = client.get(f"/v1/result/{task_id}/document", headers=auth_headers)
    assert doc.status_code == 200
    document = doc.json()["data"]
    assert document["sections"]
    assert document["spans"]


def test_check_upload_accepts_mineru_file(auth_headers, tmp_path):
    maker = tmp_path / "sample.md"
    maker.write_text("# 标题\n\n摘 要: 测试摘要内容。\n", encoding="utf-8")
    mineru = tmp_path / "sample_mineru.md"
    mineru.write_text("<table><tr><td>表格</td></tr></table>", encoding="utf-8")

    with maker.open("rb") as main, mineru.open("rb") as aux:
        upload = client.post(
            "/v1/check",
            headers=auth_headers,
            files={
                "file": ("sample.md", main, "text/markdown"),
                "mineru_file": ("sample_mineru.md", aux, "text/markdown"),
            },
            data={"rule_base_id": "generic"},
        )

    assert upload.status_code == 202
    assert upload.json()["data"]["task_id"]


def test_result_not_ready(auth_headers, tmp_path):
    maker = tmp_path / "pending.md"
    maker.write_text("# t\n\n摘 要: x\n", encoding="utf-8")
    with maker.open("rb") as f:
        upload = client.post(
            "/v1/check",
            headers=auth_headers,
            files={"file": ("pending.md", f, "text/markdown")},
            data={"rule_base_id": "generic"},
        )
    task_id = upload.json()["data"]["task_id"]
    # May race; if already done, skip
    res = client.get(f"/v1/result/{task_id}", headers=auth_headers)
    if res.status_code == 409:
        assert res.json()["code"] == "TASK_NOT_READY"
