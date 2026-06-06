from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_final_live_acceptance_stops_at_full_config_preflight(tmp_path: Path) -> None:
    log_dir = tmp_path / "logs"
    env = {
        **os.environ,
        "MSE_ACCEPTANCE_LOG_DIR": str(log_dir),
        "MSE_SAMPLE_MANIFEST": str(tmp_path / "missing-manifest.yaml"),
        "MSE_PUBLIC_THESIS_PDF": str(tmp_path / "missing-public-thesis.pdf"),
        "LLM_API_KEY": "deepseek-secret",
        "WEBHOOK_URL": "https://example.invalid/secret-token",
        "NOTIFIER": "smtp",
        "SMTP_HOST": "smtp.example.invalid",
        "SMTP_TEST_STU": "student@example.invalid",
    }

    result = subprocess.run(
        ["bash", "scripts/mse_acceptance_final_live.sh"],
        cwd=ROOT,
        env=env,
        text=True,
        capture_output=True,
        timeout=30,
    )

    combined = result.stdout + result.stderr
    assert result.returncode == 1
    assert "FAIL: config status" in result.stdout
    assert f"LOG: {log_dir / 'config_status.log'}" in result.stdout
    assert "secret-token" not in combined


def test_final_live_acceptance_enables_extra_live_stages_after_preflight(tmp_path: Path) -> None:
    fake_bin = tmp_path / "bin"
    fake_bin.mkdir()
    real_python = sys.executable
    (fake_bin / "python3").write_text(
        "#!/bin/bash\n"
        "if [[ ${1:-} == scripts/mse_config_status.py ]]; then exit 0; fi\n"
        f"exec {real_python} \"$@\"\n",
        encoding="utf-8",
    )
    (fake_bin / "python3").chmod(0o755)
    (fake_bin / "bash").write_text(
        "#!/bin/bash\n"
        "if [[ ${1:-} == scripts/mse_acceptance_quasi_prod.sh ]]; then\n"
        "  echo \"EXTRA=${MSE_ACCEPTANCE_EXTRA_LIVE:-}\" > \"$MSE_ACCEPTANCE_MARKER\"\n"
        "  exit 0\n"
        "fi\n"
        "exec /bin/bash \"$@\"\n",
        encoding="utf-8",
    )
    (fake_bin / "bash").chmod(0o755)
    marker = tmp_path / "marker.txt"
    log_dir = tmp_path / "logs"
    env = {
        **os.environ,
        "PATH": f"{fake_bin}{os.pathsep}{os.environ.get('PATH', '')}",
        "MSE_ACCEPTANCE_LOG_DIR": str(log_dir),
        "MSE_ACCEPTANCE_MARKER": str(marker),
        "WEBHOOK_URL": "https://example.invalid/secret-token",
    }

    result = subprocess.run(
        ["/bin/bash", "scripts/mse_acceptance_final_live.sh"],
        cwd=ROOT,
        env=env,
        text=True,
        capture_output=True,
        timeout=30,
    )

    combined = result.stdout + result.stderr
    assert result.returncode == 0, combined
    assert marker.read_text(encoding="utf-8").strip() == "EXTRA=1"
    assert "OK: final live acceptance" in result.stdout
    assert "secret-token" not in combined


def test_quasi_prod_extra_live_branch_runs_private_sample_and_webhook_stages() -> None:
    script = (ROOT / "scripts" / "mse_acceptance_quasi_prod.sh").read_text(encoding="utf-8")

    assert 'MSE_ACCEPTANCE_EXTRA_LIVE:-0' in script
    assert 'run_stage "private sample live acceptance" python3 scripts/mse_acceptance_private_samples.py' in script
    assert "MSE_REQUIRE_WEBHOOK_LIVE" in script
    assert 'ok "webhook live acceptance deferred"' in script
    assert 'run_stage "webhook live acceptance" python3 scripts/mse_acceptance_webhook_live.py' in script
