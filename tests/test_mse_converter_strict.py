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


def test_strict_mode_rejects_stub_converter_output(tmp_path, monkeypatch):
    pdf = tmp_path / "paper.pdf"
    pdf.write_bytes(b"%PDF-1.4\n")
    out = tmp_path / "out"

    def fake_run(cmd, **kwargs):
        output = out / Path(cmd[-1]).name
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(
            f"# Converted by {'Maker' if 'maker' in cmd[-3] else 'MinerU'} stub\n",
            encoding="utf-8",
        )

    monkeypatch.setattr("worker.converter.shutil.which", lambda _: "/usr/bin/docker")
    monkeypatch.setattr("worker.converter.subprocess.run", fake_run)

    converter = PDFConverter()
    with pytest.raises(RuntimeError, match="stub|MinerU"):
        converter.convert(pdf, out)


def test_strict_mode_requires_nonempty_mineru_output(tmp_path, monkeypatch):
    pdf = tmp_path / "paper.pdf"
    pdf.write_bytes(b"%PDF-1.4\n")
    out = tmp_path / "out"

    def fake_run(cmd, **kwargs):
        output = out / Path(cmd[-1]).name
        output.parent.mkdir(parents=True, exist_ok=True)
        if output.name == "paper_maker.md":
            output.write_text("# Real maker output\n\n正文", encoding="utf-8")
        else:
            output.write_text(" \n", encoding="utf-8")

    monkeypatch.setattr("worker.converter.shutil.which", lambda _: "/usr/bin/docker")
    monkeypatch.setattr("worker.converter.subprocess.run", fake_run)

    converter = PDFConverter()
    with pytest.raises(RuntimeError, match="MinerU"):
        converter.convert(pdf, out)


def test_mineru_docker_receives_page_window_and_resource_env(tmp_path, monkeypatch):
    pdf = tmp_path / "paper.pdf"
    pdf.write_bytes(b"%PDF-1.4\n")
    out = tmp_path / "out"
    commands: list[list[str]] = []

    monkeypatch.setenv("MINERU_START_PAGE", "0")
    monkeypatch.setenv("MINERU_END_PAGE", "7")
    monkeypatch.setenv("MINERU_DOCKER_SHM_SIZE", "2g")
    monkeypatch.setenv("MINERU_PDF_RENDER_THREADS", "1")
    monkeypatch.setenv("MINERU_PROCESSING_WINDOW_SIZE", "8")
    monkeypatch.setenv("MINERU_FORMULA_ENABLE", "false")
    monkeypatch.setenv("MINERU_TABLE_ENABLE", "false")

    def fake_run(cmd, **kwargs):
        commands.append(cmd)
        output = out / Path(cmd[-1]).name
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text("# Real output\n\n正文", encoding="utf-8")

    monkeypatch.setattr("worker.converter.shutil.which", lambda _: "/usr/bin/docker")
    monkeypatch.setattr("worker.converter.subprocess.run", fake_run)

    converter = PDFConverter()
    converter.convert(pdf, out)

    maker_cmd = commands[0]
    assert "MAKER_START_PAGE=0" in maker_cmd
    assert "MAKER_END_PAGE=7" in maker_cmd
    mineru_cmd = commands[-1]
    assert "--shm-size" in mineru_cmd
    assert "2g" in mineru_cmd
    for expected in (
        "MINERU_START_PAGE=0",
        "MINERU_END_PAGE=7",
        "MINERU_PDF_RENDER_THREADS=1",
        "MINERU_PROCESSING_WINDOW_SIZE=8",
        "MINERU_FORMULA_ENABLE=false",
        "MINERU_TABLE_ENABLE=false",
    ):
        assert expected in mineru_cmd


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
