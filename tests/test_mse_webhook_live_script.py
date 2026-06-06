from __future__ import annotations

import os
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_webhook_live_rejects_invalid_url_without_leaking_secret() -> None:
    env = {
        **os.environ,
        "PYTHONPATH": "packages:apps",
        "WEBHOOK_KIND": "feishu",
        "WEBHOOK_URL": "ftp://example.invalid/secret-token",
    }

    result = subprocess.run(
        ["python3", "scripts/mse_acceptance_webhook_live.py"],
        cwd=ROOT,
        env=env,
        text=True,
        capture_output=True,
        timeout=30,
    )

    combined = result.stdout + result.stderr
    assert result.returncode == 2
    assert "CONFIG_REQUIRED:" in result.stdout
    assert "WEBHOOK_URL must be http or https" in result.stdout
    assert "secret-token" not in combined


def test_webhook_live_failure_does_not_print_url_secret() -> None:
    env = {
        **os.environ,
        "PYTHONPATH": "packages:apps",
        "WEBHOOK_KIND": "feishu",
        "WEBHOOK_URL": "https://127.0.0.1:9/secret-token",
        "WEBHOOK_TIMEOUT_SECONDS": "0.2",
    }

    result = subprocess.run(
        ["python3", "scripts/mse_acceptance_webhook_live.py"],
        cwd=ROOT,
        env=env,
        text=True,
        capture_output=True,
        timeout=30,
    )

    combined = result.stdout + result.stderr
    assert result.returncode == 1
    assert "FAIL: webhook live acceptance" in result.stdout
    assert "secret-token" not in combined
    assert "https://127.0.0.1" not in combined
