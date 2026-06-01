from __future__ import annotations

import os
from pathlib import Path

import pytest

from worker.converter import PDFConverter


@pytest.fixture(autouse=True)
def _strict_mode(monkeypatch):
    monkeypatch.setenv("MSE_ALLOW_MOCK_FALLBACK", "0")
    monkeypatch.setenv("PDF_CONVERTER_MODE", "docker")


def test_strict_mode_raises_without_docker(tmp_path, monkeypatch):
    monkeypatch.delenv("PATH", raising=False)
    pdf = tmp_path / "paper.pdf"
    pdf.write_bytes(b"%PDF-1.4\n")
    out = tmp_path / "out"
    converter = PDFConverter()
    with pytest.raises(RuntimeError, match="docker|MSE_ALLOW_MOCK_FALLBACK"):
        converter.convert(pdf, out)
    assert not (out / "paper_maker.md").exists()


def test_strict_mode_docker_failure_no_mock(tmp_path, monkeypatch):
    pdf = tmp_path / "paper.pdf"
    pdf.write_bytes(b"%PDF-1.4\n")
    out = tmp_path / "out"

    def fake_run(*args, **kwargs):
        raise FileNotFoundError("docker failed")

    monkeypatch.setattr("worker.converter.shutil.which", lambda _: "/usr/bin/docker")
    monkeypatch.setattr("worker.converter.subprocess.run", fake_run)

    converter = PDFConverter()
    with pytest.raises(RuntimeError, match="docker conversion failed|PDF conversion failed"):
        converter.convert(pdf, out)
    assert not (out / "paper_maker.md").exists()


def test_mock_allowed_when_env_set(tmp_path, monkeypatch):
    monkeypatch.setenv("MSE_ALLOW_MOCK_FALLBACK", "1")
    monkeypatch.setenv("PDF_CONVERTER_MODE", "mock")
    pdf = tmp_path / "paper.pdf"
    pdf.write_bytes(b"%PDF-1.4\n")
    out = tmp_path / "out"
    converter = PDFConverter()
    maker, _ = converter.convert(pdf, out)
    assert maker.exists()
    assert maker.read_text(encoding="utf-8")
