from __future__ import annotations

import subprocess
from pathlib import Path

import yaml
from reportlab.pdfgen import canvas


ROOT = Path(__file__).resolve().parents[1]


def _write_pdf(path: Path, text: str = "PDF") -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    pdf = canvas.Canvas(str(path))
    pdf.drawString(72, 760, text)
    pdf.save()


def _write_manifest(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        """
version: 1
discipline: computer_science
tiers:
  - id: tier-a-primary
    tier: A
    primary: true
    school: 待填写学校
    subfield: traffic_prediction
    thesis_pdf: theses/tier-a-primary.pdf
    spec_file: specs/tier-a-primary.md
  - id: tier-b-placeholder
    tier: B
    primary: false
    thesis_pdf: theses/tier-b-placeholder.pdf
    spec_file: specs/tier-b-placeholder.md
""".strip(),
        encoding="utf-8",
    )


def test_import_private_sample_copies_files_and_updates_manifest(tmp_path: Path) -> None:
    manifest = tmp_path / "samples" / "mse" / "manifest.yaml"
    _write_manifest(manifest)
    thesis = tmp_path / "downloads" / "cnki.pdf"
    spec = tmp_path / "downloads" / "school-spec.pdf"
    _write_pdf(thesis, "CNKI CS thesis")
    _write_pdf(spec, "College thesis specification")

    result = subprocess.run(
        [
            "python3",
            "scripts/mse_import_private_sample.py",
            "--manifest",
            str(manifest),
            "--pdf",
            str(thesis),
            "--spec",
            str(spec),
            "--school",
            "Example University",
            "--subfield",
            "software_engineering",
        ],
        cwd=ROOT,
        text=True,
        capture_output=True,
        timeout=30,
    )

    assert result.returncode == 0, result.stderr + result.stdout
    assert (manifest.parent / "theses" / "tier-a-primary.pdf").read_bytes() == thesis.read_bytes()
    assert (manifest.parent / "specs" / "tier-a-primary.pdf").read_bytes() == spec.read_bytes()
    raw = yaml.safe_load(manifest.read_text(encoding="utf-8"))
    primary = raw["tiers"][0]
    assert primary["school"] == "Example University"
    assert primary["subfield"] == "software_engineering"
    assert primary["thesis_pdf"] == "theses/tier-a-primary.pdf"
    assert primary["spec_file"] == "specs/tier-a-primary.pdf"
    assert "OK:" in result.stdout


def test_import_private_sample_rejects_invalid_pdf_without_overwriting(tmp_path: Path) -> None:
    manifest = tmp_path / "samples" / "mse" / "manifest.yaml"
    _write_manifest(manifest)
    target = manifest.parent / "theses" / "tier-a-primary.pdf"
    target.parent.mkdir(parents=True)
    target.write_bytes(b"%PDF-existing")
    thesis = tmp_path / "downloads" / "not-a-pdf.pdf"
    spec = tmp_path / "downloads" / "school-spec.md"
    thesis.parent.mkdir(parents=True)
    thesis.write_text("not a pdf", encoding="utf-8")
    spec.write_text("# spec\n", encoding="utf-8")

    result = subprocess.run(
        [
            "python3",
            "scripts/mse_import_private_sample.py",
            "--manifest",
            str(manifest),
            "--pdf",
            str(thesis),
            "--spec",
            str(spec),
        ],
        cwd=ROOT,
        text=True,
        capture_output=True,
        timeout=30,
    )

    assert result.returncode == 2
    assert "CONFIG_REQUIRED:" in result.stdout
    assert target.read_bytes() == b"%PDF-existing"
