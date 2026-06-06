#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import mimetypes
import sys
import time
import uuid
from pathlib import Path

import httpx

from mse.sample_manifest import validate_sample_manifest


def _rand_email(prefix: str) -> str:
    return f"{prefix}-{uuid.uuid4().hex[:8]}@local.test"


def _fail(stage: str, message: str, code: int = 1) -> int:
    print(f"FAIL: {stage}")
    print(message)
    return code


def _post_json(client: httpx.Client, path: str, payload: dict, token: str | None = None) -> dict:
    headers = {"Authorization": f"Bearer {token}"} if token else {}
    response = client.post(path, json=payload, headers=headers)
    response.raise_for_status()
    return response.json()


def _register(client: httpx.Client, role: str) -> tuple[str, str]:
    email = _rand_email(role)
    data = _post_json(
        client,
        "/v1/auth/register",
        {"email": email, "password": "secret12", "name": role, "role": role},
    )
    return data["access_token"], email


def _upload_file(
    client: httpx.Client,
    path: str,
    file_path: Path,
    *,
    token: str | None = None,
) -> dict:
    headers = {"Authorization": f"Bearer {token}"} if token else {}
    mime = mimetypes.guess_type(file_path.name)[0] or "application/octet-stream"
    with file_path.open("rb") as handle:
        response = client.post(
            path,
            headers=headers,
            files={"file": (file_path.name, handle, mime)},
        )
    response.raise_for_status()
    return response.json()


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    parser = argparse.ArgumentParser(description="Run MSE live acceptance against local private samples.")
    parser.add_argument("--api", default="http://127.0.0.1:8000")
    parser.add_argument("--manifest", default=str(root / "samples" / "mse" / "manifest.yaml"))
    parser.add_argument("--timeout", type=int, default=900)
    args = parser.parse_args()

    manifest_path = Path(args.manifest)
    validation = validate_sample_manifest(manifest_path, require_primary=True)
    if not validation.ready_primary_entries:
        print("CONFIG_REQUIRED: no ready primary MSE private sample")
        for item in validation.missing:
            print(f"MISSING: {item}")
        for item in validation.invalid:
            print(f"INVALID: {item}")
        return 2

    sample = validation.ready_primary_entries[0]
    sample_root = manifest_path.parent
    thesis_pdf = sample_root / sample.thesis_pdf
    spec_file = sample_root / sample.spec_file

    with httpx.Client(base_url=args.api, timeout=120) as client:
        try:
            health = client.get("/health")
            health.raise_for_status()
        except Exception as exc:
            return _fail("API health", f"API_REQUIRED: start API at {args.api} first ({exc})", 2)

        advisor_token, _advisor_email = _register(client, "advisor")
        student_token, student_email = _register(client, "student")

        project = _post_json(
            client,
            "/v1/mse/projects",
            {
                "title": f"M1-5 {sample.id}",
                "student_email": student_email,
                "auto_notify_student": True,
            },
            advisor_token,
        )
        project_id = project["id"]

        _upload_file(
            client,
            f"/v1/mse/projects/{project_id}/rules",
            spec_file,
            token=advisor_token,
        )
        invite = _post_json(
            client,
            f"/v1/mse/projects/{project_id}/invite",
            {"send_email": False},
            advisor_token,
        )
        _post_json(
            client,
            f"/v1/mse/projects/{project_id}/accept",
            {"token": invite["token"]},
            student_token,
        )
        submission = _upload_file(
            client,
            f"/v1/mse/projects/{project_id}/submissions",
            thesis_pdf,
            token=student_token,
        )
        round_number = submission["round_number"]
        print(f"OK: submitted {sample.id} round={round_number}")

        deadline = time.time() + args.timeout
        report = None
        while time.time() < deadline:
            response = client.get(
                f"/v1/mse/projects/{project_id}/rounds/{round_number}/report",
                headers={"Authorization": f"Bearer {advisor_token}"},
            )
            response.raise_for_status()
            report = response.json()
            status = report.get("review_status")
            print(f"status={status}")
            if status not in {"pending", "parsing", "analyzing"}:
                break
            time.sleep(5)
        if not report:
            return _fail("private sample report", "no report returned")

        status = report.get("review_status")
        if status in {"parse_failed", "analysis_failed", "failed"}:
            return _fail("private sample analysis", json.dumps(report, ensure_ascii=False)[:1000])
        if status in {"pending", "parsing", "analyzing"}:
            return _fail("private sample analysis", f"timed out after {args.timeout}s")

        issues = ((report.get("report") or {}).get("issues") or [])
        if not issues:
            return _fail("private sample issue list", "expected at least one issue")
        with_page = [issue for issue in issues if issue.get("page")]
        with_hint = [issue for issue in issues if issue.get("revision_hint")]
        if not with_page:
            return _fail("private sample issue pages", "expected at least one issue with page")
        if not with_hint:
            return _fail("private sample revision hints", "expected at least one issue with revision_hint")

        export = client.get(
            f"/v1/mse/projects/{project_id}/rounds/{round_number}/export.pdf",
            headers={"Authorization": f"Bearer {advisor_token}"},
        )
        export.raise_for_status()
        if not export.content.startswith(b"%PDF"):
            return _fail("private sample PDF export", "export.pdf is not a PDF")

        print(
            "OK: M1-5 private sample acceptance "
            f"sample={sample.id} issues={len(issues)} pages={len(with_page)} hints={len(with_hint)}"
        )
        return 0


if __name__ == "__main__":
    sys.exit(main())
