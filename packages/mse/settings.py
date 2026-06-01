from __future__ import annotations

import os


def _truthy(value: str | None, default: bool = False) -> bool:
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def allow_mock_fallback() -> bool:
    """When False, PDF/image conversion must not fall back to bundled samples."""
    return _truthy(os.getenv("MSE_ALLOW_MOCK_FALLBACK"), default=True)


def pdf_converter_mode() -> str:
    return os.getenv("PDF_CONVERTER_MODE", "auto").strip().lower()


def use_docker_converter() -> bool:
    return pdf_converter_mode() != "mock"
