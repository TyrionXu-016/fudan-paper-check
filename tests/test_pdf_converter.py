from pathlib import Path

import pytest

from worker.converter import PDFConverter


def test_docker_converter_does_not_fallback_without_docker(monkeypatch, tmp_path):
    monkeypatch.setenv("PDF_CONVERTER_MODE", "docker")
    monkeypatch.setattr("worker.converter.shutil.which", lambda _: None)

    pdf = tmp_path / "paper.pdf"
    pdf.write_bytes(b"%PDF-1.4\n")
    out_dir = tmp_path / "out"

    with pytest.raises(RuntimeError, match="docker CLI is required"):
        PDFConverter().convert(pdf, out_dir)

    assert not (out_dir / "paper_maker.md").exists()
