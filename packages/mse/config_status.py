from __future__ import annotations

import os
import shlex
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable, Mapping

from mse.public_thesis import DEFAULT_PUBLIC_THESIS_PDF_PATH, validate_public_thesis_pdf
from mse.sample_manifest import validate_sample_manifest
from notify.webhook import validate_webhook_url


DEFAULT_MANIFEST_PATH = Path(__file__).resolve().parents[2] / "samples" / "mse" / "manifest.yaml"


@dataclass(frozen=True)
class ConfigCheck:
    id: str
    label: str
    status: str
    details: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "label": self.label,
            "status": self.status,
            "details": list(self.details),
        }


@dataclass(frozen=True)
class ConfigStatus:
    checks: list[ConfigCheck]

    @property
    def ready(self) -> bool:
        return all(check.status == "ready" for check in self.checks)

    def to_dict(self) -> dict:
        return {
            "ready": self.ready,
            "checks": [check.to_dict() for check in self.checks],
        }


def load_status_env(
    env_files: Iterable[str | Path] | None = None,
    *,
    base_env: Mapping[str, str] | None = None,
) -> dict[str, str]:
    merged = dict(os.environ if base_env is None else base_env)
    for env_file in env_files or []:
        path = Path(env_file)
        if not path.exists():
            continue
        merged.update(_read_env_file(path))
    return merged


def build_config_status(
    *,
    manifest_path: str | Path = DEFAULT_MANIFEST_PATH,
    public_pdf_path: str | Path = DEFAULT_PUBLIC_THESIS_PDF_PATH,
    env: Mapping[str, str] | None = None,
    require_private_samples: bool = True,
    require_webhook: bool = True,
    require_public_pdf: bool = True,
    require_quasi_prod: bool = True,
) -> ConfigStatus:
    effective_env = dict(os.environ if env is None else env)
    checks = []
    if require_private_samples:
        checks.append(_check_private_samples(Path(manifest_path)))
    if require_public_pdf:
        checks.append(_check_public_thesis_pdf(Path(public_pdf_path)))
    if require_webhook:
        checks.append(_check_webhook_live(effective_env))
    if require_quasi_prod:
        checks.append(_check_quasi_prod_env(effective_env))
    return ConfigStatus(checks=checks)


def _check_private_samples(manifest_path: Path) -> ConfigCheck:
    validation = validate_sample_manifest(manifest_path, require_primary=True)
    if validation.ready_primary_entries:
        return ConfigCheck(
            id="m1_5_private_samples",
            label="M1-5 CNKI/private sample PDF and spec",
            status="ready",
            details=[f"{validation.primary_ready_count} primary sample(s) ready"],
        )

    details = validation.missing + validation.invalid
    if not details:
        details = ["at least one primary sample with thesis_pdf and spec_file is required"]
    return ConfigCheck(
        id="m1_5_private_samples",
        label="M1-5 CNKI/private sample PDF and spec",
        status="config_required",
        details=details,
    )


def _check_public_thesis_pdf(public_pdf_path: Path) -> ConfigCheck:
    validation = validate_public_thesis_pdf(public_pdf_path)
    if validation.ready:
        return ConfigCheck(
            id="public_thesis_pdf",
            label="Dartmouth public CS master's thesis PDF",
            status="ready",
            details=["public Dartmouth thesis PDF is present and validated"],
        )
    return ConfigCheck(
        id="public_thesis_pdf",
        label="Dartmouth public CS master's thesis PDF",
        status="config_required",
        details=[
            f"{public_pdf_path}: {validation.reason}",
            "run scripts/download_mse_public_thesis_pdf.sh or manually place the Dartmouth PDF",
        ],
    )


def _check_webhook_live(env: Mapping[str, str]) -> ConfigCheck:
    details: list[str] = []
    kind = _get(env, "WEBHOOK_KIND") or "feishu"
    url = _get(env, "WEBHOOK_URL")
    if not url:
        details.append("WEBHOOK_URL is required for live Feishu/WeCom webhook acceptance")
    elif validation_error := validate_webhook_url(url):
        details.append(validation_error)
    if kind.lower() not in {"feishu", "wecom"}:
        details.append("WEBHOOK_KIND must be feishu or wecom")
    if details:
        return ConfigCheck(
            id="webhook_live",
            label="Feishu/WeCom webhook live acceptance",
            status="config_required",
            details=details,
        )
    return ConfigCheck(
        id="webhook_live",
        label="Feishu/WeCom webhook live acceptance",
        status="ready",
        details=[f"WEBHOOK_KIND={kind.lower()}", "WEBHOOK_URL is configured"],
    )


def _check_quasi_prod_env(env: Mapping[str, str]) -> ConfigCheck:
    details: list[str] = []
    if not _get(env, "LLM_API_KEY"):
        details.append("LLM_API_KEY is required for DeepSeek live acceptance")
    if (_get(env, "NOTIFIER") or "").lower() != "smtp":
        details.append("NOTIFIER must be smtp for quasi-production acceptance")
    if not _get(env, "SMTP_HOST"):
        details.append("SMTP_HOST is required for SMTP live acceptance")
    if not (_get(env, "SMTP_TEST_STU") or _get(env, "SMTP_USER") or _get(env, "SMTP_FROM")):
        details.append("SMTP_TEST_STU is required, or provide SMTP_USER/SMTP_FROM as fallback")
    if (_get(env, "PDF_CONVERTER_MODE") or "").lower() != "docker":
        details.append("PDF_CONVERTER_MODE must be docker")
    if _get(env, "MSE_ALLOW_MOCK_FALLBACK") != "0":
        details.append("MSE_ALLOW_MOCK_FALLBACK must be 0")
    if details:
        return ConfigCheck(
            id="quasi_prod_env",
            label="Local quasi-production DeepSeek/SMTP/strict converter env",
            status="config_required",
            details=details,
        )
    return ConfigCheck(
        id="quasi_prod_env",
        label="Local quasi-production DeepSeek/SMTP/strict converter env",
        status="ready",
        details=[
            "DeepSeek live key is present",
            "SMTP live settings are present",
            "strict Docker converter mode is configured",
        ],
    )


def _get(env: Mapping[str, str], key: str) -> str:
    return str(env.get(key) or "").strip()


def _read_env_file(path: Path) -> dict[str, str]:
    try:
        from dotenv import dotenv_values
    except ImportError:
        return _read_env_file_simple(path)
    return {k: str(v) for k, v in dotenv_values(path).items() if k and v is not None}


def _read_env_file_simple(path: Path) -> dict[str, str]:
    values: dict[str, str] = {}
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("export "):
            line = line[len("export ") :].strip()
        if "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        if not key:
            continue
        try:
            parsed = shlex.split(value, comments=True, posix=True)
        except ValueError:
            parsed = [value.strip()]
        values[key] = parsed[0] if parsed else ""
    return values
