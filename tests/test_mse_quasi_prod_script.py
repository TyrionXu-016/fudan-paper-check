from __future__ import annotations

import os
import subprocess
from pathlib import Path


def test_quasi_prod_acceptance_runs_config_preflight_before_docker_work(tmp_path: Path) -> None:
    fake_bin = tmp_path / "bin"
    fake_bin.mkdir()
    docker = fake_bin / "docker"
    docker.write_text(
        "#!/usr/bin/env bash\n"
        "if [[ ${1:-} == info ]]; then exit 0; fi\n"
        "echo unexpected docker command: \"$@\" >&2\n"
        "exit 99\n",
        encoding="utf-8",
    )
    docker.chmod(0o755)
    log_dir = tmp_path / "logs"
    env = {
        **os.environ,
        "PATH": f"{fake_bin}{os.pathsep}{os.environ.get('PATH', '')}",
        "MSE_ACCEPTANCE_LOG_DIR": str(log_dir),
        "MSE_PUBLIC_THESIS_PDF": str(tmp_path / "missing-public-thesis.pdf"),
        "LLM_API_KEY": "deepseek-secret",
        "NOTIFIER": "smtp",
        "SMTP_HOST": "smtp.example.invalid",
        "SMTP_TEST_STU": "student@example.invalid",
    }

    result = subprocess.run(
        ["bash", "scripts/mse_acceptance_quasi_prod.sh"],
        cwd=Path(__file__).resolve().parents[1],
        env=env,
        text=True,
        capture_output=True,
        timeout=30,
    )

    assert result.returncode == 1
    assert "FAIL: config status" in result.stdout
    assert f"LOG: {log_dir / 'config_status.log'}" in result.stdout
    assert "deepseek-secret" not in result.stdout + result.stderr
    log = log_dir / "config_status.log"
    assert log.exists()
    log_text = log.read_text(encoding="utf-8")
    assert "public_thesis_pdf" in log_text
    assert "Dartmouth public CS master's thesis PDF" in log_text
    assert "unrecognized arguments" not in log_text
