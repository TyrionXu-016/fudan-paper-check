from __future__ import annotations

from pathlib import Path

from mse.sample_manifest import validate_sample_manifest


def test_sample_manifest_accepts_complete_primary_sample(tmp_path: Path) -> None:
    root = tmp_path / "samples" / "mse"
    (root / "theses").mkdir(parents=True)
    (root / "specs").mkdir()
    (root / "theses" / "sample.pdf").write_bytes(b"%PDF-1.4\n")
    (root / "specs" / "school.md").write_text("# 论文规范\n", encoding="utf-8")
    manifest = root / "manifest.yaml"
    manifest.write_text(
        """
version: 1
discipline: computer_science
tiers:
  - id: cnki-a-1
    tier: A
    primary: true
    school: Example University
    subfield: software_engineering
    thesis_pdf: theses/sample.pdf
    spec_file: specs/school.md
""".strip(),
        encoding="utf-8",
    )

    result = validate_sample_manifest(manifest, require_primary=True)

    assert result.ready
    assert result.primary_ready_count == 1
    assert [entry.id for entry in result.ready_primary_entries] == ["cnki-a-1"]
    assert result.missing == []


def test_sample_manifest_reports_missing_primary_files(tmp_path: Path) -> None:
    root = tmp_path / "samples" / "mse"
    root.mkdir(parents=True)
    manifest = root / "manifest.yaml"
    manifest.write_text(
        """
version: 1
discipline: computer_science
tiers:
  - id: cnki-a-1
    tier: A
    primary: true
    school: Example University
    subfield: nlp
    thesis_pdf: theses/missing.pdf
    spec_file: specs/missing.md
""".strip(),
        encoding="utf-8",
    )

    result = validate_sample_manifest(manifest, require_primary=True)

    assert not result.ready
    assert result.primary_ready_count == 0
    assert "cnki-a-1 thesis_pdf theses/missing.pdf" in result.missing
    assert "cnki-a-1 spec_file specs/missing.md" in result.missing


def test_sample_manifest_rejects_invalid_pdf_spec(tmp_path: Path) -> None:
    root = tmp_path / "samples" / "mse"
    (root / "theses").mkdir(parents=True)
    (root / "specs").mkdir()
    (root / "theses" / "sample.pdf").write_bytes(b"%PDF-1.4\n")
    (root / "specs" / "school.pdf").write_text("not a pdf", encoding="utf-8")
    manifest = root / "manifest.yaml"
    manifest.write_text(
        """
version: 1
discipline: computer_science
tiers:
  - id: cnki-a-1
    tier: A
    primary: true
    thesis_pdf: theses/sample.pdf
    spec_file: specs/school.pdf
""".strip(),
        encoding="utf-8",
    )

    result = validate_sample_manifest(manifest, require_primary=True)

    assert not result.ready
    assert "cnki-a-1 spec_file specs/school.pdf is not a PDF" in result.invalid
