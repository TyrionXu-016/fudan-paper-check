from __future__ import annotations

import json
from pathlib import Path

from reportlab.pdfgen import canvas

from mse.config_status import build_config_status


def _write_manifest(root: Path, *, create_files: bool) -> Path:
    sample_root = root / "samples" / "mse"
    sample_root.mkdir(parents=True)
    if create_files:
        (sample_root / "theses").mkdir()
        (sample_root / "specs").mkdir()
        (sample_root / "theses" / "tier-a.pdf").write_bytes(b"%PDF-1.4\n")
        (sample_root / "specs" / "tier-a.md").write_text("# 论文规范\n", encoding="utf-8")
    manifest = sample_root / "manifest.yaml"
    manifest.write_text(
        """
version: 1
discipline: computer_science
tiers:
  - id: tier-a-primary
    tier: A
    primary: true
    school: Example University
    subfield: software_engineering
    thesis_pdf: theses/tier-a.pdf
    spec_file: specs/tier-a.md
""".strip(),
        encoding="utf-8",
    )
    return manifest


def _write_public_thesis_pdf(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    pdf = canvas.Canvas(str(path))
    pdf.drawString(72, 760, "Chinese Font Style Transfer with Neural Network")
    pdf.drawString(72, 740, "Xue Hanyu, Dartmouth College")
    pdf.save()


def test_config_status_reports_missing_external_requirements(tmp_path: Path) -> None:
    manifest = _write_manifest(tmp_path, create_files=False)
    public_pdf = tmp_path / "public.pdf"

    status = build_config_status(manifest_path=manifest, public_pdf_path=public_pdf, env={})

    assert not status.ready
    checks = {check.id: check for check in status.checks}
    assert checks["m1_5_private_samples"].status == "config_required"
    assert checks["public_thesis_pdf"].status == "config_required"
    assert checks["webhook_live"].status == "config_required"
    assert checks["quasi_prod_env"].status == "config_required"
    assert "LLM_API_KEY" in " ".join(checks["quasi_prod_env"].details)


def test_config_status_is_ready_when_samples_and_live_env_are_configured(tmp_path: Path) -> None:
    manifest = _write_manifest(tmp_path, create_files=True)
    public_pdf = tmp_path / "public.pdf"
    _write_public_thesis_pdf(public_pdf)
    env = {
        "WEBHOOK_KIND": "feishu",
        "WEBHOOK_URL": "https://example.invalid/webhook/secret-token",
        "LLM_API_KEY": "deepseek-secret",
        "NOTIFIER": "smtp",
        "SMTP_HOST": "smtp.example.invalid",
        "SMTP_TEST_STU": "student@example.invalid",
        "PDF_CONVERTER_MODE": "docker",
        "MSE_ALLOW_MOCK_FALLBACK": "0",
    }

    status = build_config_status(manifest_path=manifest, public_pdf_path=public_pdf, env=env)

    assert status.ready
    assert {check.status for check in status.checks} == {"ready"}
    payload = json.dumps(status.to_dict(), ensure_ascii=False)
    assert "deepseek-secret" not in payload
    assert "secret-token" not in payload


def test_config_status_can_skip_quasi_prod_env_when_only_external_assets_are_needed(
    tmp_path: Path,
) -> None:
    manifest = _write_manifest(tmp_path, create_files=True)
    public_pdf = tmp_path / "public.pdf"
    _write_public_thesis_pdf(public_pdf)
    env = {
        "WEBHOOK_KIND": "wecom",
        "WEBHOOK_URL": "https://example.invalid/webhook",
    }

    status = build_config_status(
        manifest_path=manifest,
        public_pdf_path=public_pdf,
        env=env,
        require_quasi_prod=False,
    )

    assert status.ready
    assert [check.id for check in status.checks] == [
        "m1_5_private_samples",
        "public_thesis_pdf",
        "webhook_live",
    ]


def test_config_status_quasi_prod_profile_only_requires_env_and_public_pdf(
    tmp_path: Path,
) -> None:
    manifest = _write_manifest(tmp_path, create_files=False)
    public_pdf = tmp_path / "public.pdf"
    _write_public_thesis_pdf(public_pdf)
    env = {
        "LLM_API_KEY": "deepseek-secret",
        "NOTIFIER": "smtp",
        "SMTP_HOST": "smtp.example.invalid",
        "SMTP_TEST_STU": "student@example.invalid",
        "PDF_CONVERTER_MODE": "docker",
        "MSE_ALLOW_MOCK_FALLBACK": "0",
    }

    status = build_config_status(
        manifest_path=manifest,
        public_pdf_path=public_pdf,
        env=env,
        require_private_samples=False,
        require_webhook=False,
    )

    assert status.ready
    assert [check.id for check in status.checks] == ["public_thesis_pdf", "quasi_prod_env"]


def test_config_status_rejects_wrong_public_thesis_pdf(tmp_path: Path) -> None:
    manifest = _write_manifest(tmp_path, create_files=True)
    public_pdf = tmp_path / "wrong.pdf"
    public_pdf.parent.mkdir(parents=True, exist_ok=True)
    pdf = canvas.Canvas(str(public_pdf))
    pdf.drawString(72, 760, "An unrelated public thesis")
    pdf.save()
    env = {
        "WEBHOOK_KIND": "feishu",
        "WEBHOOK_URL": "https://example.invalid/webhook",
        "LLM_API_KEY": "deepseek-secret",
        "NOTIFIER": "smtp",
        "SMTP_HOST": "smtp.example.invalid",
        "SMTP_TEST_STU": "student@example.invalid",
        "PDF_CONVERTER_MODE": "docker",
        "MSE_ALLOW_MOCK_FALLBACK": "0",
    }

    status = build_config_status(manifest_path=manifest, public_pdf_path=public_pdf, env=env)

    checks = {check.id: check for check in status.checks}
    assert not status.ready
    assert checks["public_thesis_pdf"].status == "config_required"
    assert "does not look like the Dartmouth thesis" in " ".join(checks["public_thesis_pdf"].details)


def test_config_status_rejects_invalid_webhook_url_without_leaking_secret(
    tmp_path: Path,
) -> None:
    manifest = _write_manifest(tmp_path, create_files=True)
    public_pdf = tmp_path / "public.pdf"
    _write_public_thesis_pdf(public_pdf)
    env = {
        "WEBHOOK_KIND": "feishu",
        "WEBHOOK_URL": "ftp://example.invalid/secret-token",
        "LLM_API_KEY": "deepseek-secret",
        "NOTIFIER": "smtp",
        "SMTP_HOST": "smtp.example.invalid",
        "SMTP_TEST_STU": "student@example.invalid",
        "PDF_CONVERTER_MODE": "docker",
        "MSE_ALLOW_MOCK_FALLBACK": "0",
    }

    status = build_config_status(manifest_path=manifest, public_pdf_path=public_pdf, env=env)

    checks = {check.id: check for check in status.checks}
    payload = json.dumps(status.to_dict(), ensure_ascii=False)
    assert not status.ready
    assert checks["webhook_live"].status == "config_required"
    assert "WEBHOOK_URL must be http or https" in " ".join(checks["webhook_live"].details)
    assert "secret-token" not in payload
