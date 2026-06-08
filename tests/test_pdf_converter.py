from pathlib import Path

import pytest

from worker.converter import PDFConverter, _normalise_maker_markdown


def test_docker_converter_does_not_fallback_without_docker(monkeypatch, tmp_path):
    monkeypatch.setenv("PDF_CONVERTER_MODE", "docker")
    monkeypatch.setattr(
        PDFConverter,
        "_docker_client",
        staticmethod(lambda: (_ for _ in ()).throw(RuntimeError("docker unavailable"))),
    )

    pdf = tmp_path / "paper.pdf"
    pdf.write_bytes(b"%PDF-1.4\n")
    out_dir = tmp_path / "out"

    with pytest.raises(RuntimeError, match="docker unavailable"):
        PDFConverter().convert(pdf, out_dir)

    assert not (out_dir / "paper_maker.md").exists()


def test_maker_markdown_normalisation_adds_body_section(tmp_path):
    md = tmp_path / "paper_maker.md"
    pdf = tmp_path / "uploaded.pdf"
    md.write_text(
        "# Converted by Maker-compatible text extractor from uploaded.pdf\n\n"
        "第一段正文。\n第二段正文。\n",
        encoding="utf-8",
    )

    _normalise_maker_markdown(md, pdf)

    text = md.read_text(encoding="utf-8")
    assert text.startswith("# uploaded\n")
    assert "\n## 正文\n" in text
    assert "第一段正文。" in text
