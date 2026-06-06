from __future__ import annotations

import os
import subprocess
from pathlib import Path


def test_public_thesis_downloader_does_not_fallback_to_non_dartmouth_pdf(tmp_path: Path) -> None:
    page = tmp_path / "page.html"
    missing_pdf = tmp_path / "missing.pdf"
    fallback_pdf = tmp_path / "fallback.pdf"
    output_pdf = tmp_path / "out.pdf"
    fallback_pdf.write_bytes(b"%PDF-1.4\nnot the Dartmouth thesis\n")
    page.write_text(
        f'<html><head><meta name="bepress_citation_pdf_url" content="{missing_pdf.as_uri()}"></head></html>',
        encoding="utf-8",
    )

    env = {
        **os.environ,
        "MSE_PUBLIC_THESIS_PAGE_URL": page.as_uri(),
        "MSE_PUBLIC_THESIS_FALLBACK_URL": fallback_pdf.as_uri(),
        "MINERU_TEST_PDF": str(output_pdf),
    }

    result = subprocess.run(
        ["bash", "scripts/download_mse_public_thesis_pdf.sh"],
        cwd=Path(__file__).resolve().parents[1],
        env=env,
        text=True,
        capture_output=True,
        timeout=30,
    )

    assert result.returncode != 0
    assert not output_pdf.exists()
    assert "could not download Dartmouth thesis PDF" in (result.stderr + result.stdout)


def test_public_thesis_downloader_rejects_existing_wrong_pdf(tmp_path: Path) -> None:
    page = tmp_path / "page.html"
    output_pdf = tmp_path / "out.pdf"
    output_pdf.write_bytes(b"%PDF-1.4\nnot the Dartmouth thesis\n")
    page.write_text(
        '<html><head><meta name="bepress_citation_pdf_url" content="file:///missing.pdf"></head></html>',
        encoding="utf-8",
    )

    env = {
        **os.environ,
        "MSE_PUBLIC_THESIS_PAGE_URL": page.as_uri(),
        "MINERU_TEST_PDF": str(output_pdf),
    }

    result = subprocess.run(
        ["bash", "scripts/download_mse_public_thesis_pdf.sh"],
        cwd=Path(__file__).resolve().parents[1],
        env=env,
        text=True,
        capture_output=True,
        timeout=30,
    )

    assert result.returncode != 0
    assert "does not look like the Dartmouth thesis" in (result.stderr + result.stdout)
