from __future__ import annotations

import subprocess
from pathlib import Path

from reportlab.pdfgen import canvas


ROOT = Path(__file__).resolve().parents[1]


def _write_pdf(path: Path, lines: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    pdf = canvas.Canvas(str(path))
    y = 760
    for line in lines:
        pdf.drawString(72, y, line)
        y -= 20
    pdf.save()


def test_import_public_thesis_copies_valid_dartmouth_pdf(tmp_path: Path) -> None:
    source = tmp_path / "downloaded.pdf"
    target = tmp_path / "public_cs_master_thesis.pdf"
    _write_pdf(
        source,
        [
            "Chinese Font Style Transfer with Neural Network",
            "Xue Hanyu",
            "Dartmouth College",
        ],
    )

    result = subprocess.run(
        [
            "python3",
            "scripts/mse_import_public_thesis_pdf.py",
            str(source),
            "--target",
            str(target),
        ],
        cwd=ROOT,
        text=True,
        capture_output=True,
        timeout=30,
    )

    assert result.returncode == 0, result.stderr + result.stdout
    assert target.read_bytes() == source.read_bytes()
    assert "OK:" in result.stdout


def test_import_public_thesis_rejects_wrong_pdf_without_overwriting_target(tmp_path: Path) -> None:
    source = tmp_path / "wrong.pdf"
    target = tmp_path / "public_cs_master_thesis.pdf"
    _write_pdf(source, ["Unrelated thesis"])
    target.write_bytes(b"existing-good-enough-for-this-test")

    result = subprocess.run(
        [
            "python3",
            "scripts/mse_import_public_thesis_pdf.py",
            str(source),
            "--target",
            str(target),
        ],
        cwd=ROOT,
        text=True,
        capture_output=True,
        timeout=30,
    )

    assert result.returncode == 2
    assert "CONFIG_REQUIRED:" in result.stdout
    assert target.read_bytes() == b"existing-good-enough-for-this-test"
