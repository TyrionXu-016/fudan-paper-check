#!/usr/bin/env python3
from __future__ import annotations

import argparse
import shutil
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_MANIFEST = ROOT / "samples" / "mse" / "manifest.yaml"


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Validate and import a local CNKI/institution MSE thesis sample."
    )
    parser.add_argument("--manifest", default=str(DEFAULT_MANIFEST))
    parser.add_argument("--id", dest="sample_id", default="")
    parser.add_argument("--pdf", required=True, help="Local thesis PDF")
    parser.add_argument("--spec", required=True, help="Local college specification PDF or Markdown file")
    parser.add_argument("--school", default="")
    parser.add_argument("--subfield", default="")
    args = parser.parse_args()

    manifest_path = Path(args.manifest)
    thesis_source = Path(args.pdf)
    spec_source = Path(args.spec)

    errors = _validate_inputs(manifest_path, thesis_source, spec_source)
    if errors:
        for error in errors:
            print(f"CONFIG_REQUIRED: {error}")
        return 2

    raw = yaml.safe_load(manifest_path.read_text(encoding="utf-8")) or {}
    tiers = raw.get("tiers") or []
    entry = _find_entry(tiers, args.sample_id)
    if entry is None:
        print(f"CONFIG_REQUIRED: sample id {args.sample_id!r} not found")
        return 2

    sample_id = str(entry.get("id") or "").strip()
    if not sample_id:
        print("CONFIG_REQUIRED: target sample entry has no id")
        return 2

    root = manifest_path.parent
    thesis_rel = f"theses/{sample_id}.pdf"
    spec_suffix = _spec_suffix(spec_source)
    spec_rel = f"specs/{sample_id}{spec_suffix}"
    thesis_target = root / thesis_rel
    spec_target = root / spec_rel

    _copy_atomic(thesis_source, thesis_target)
    _copy_atomic(spec_source, spec_target)
    entry["thesis_pdf"] = thesis_rel
    entry["spec_file"] = spec_rel
    if args.school:
        entry["school"] = args.school
    if args.subfield:
        entry["subfield"] = args.subfield
    entry["primary"] = True

    manifest_path.write_text(
        yaml.safe_dump(raw, allow_unicode=True, sort_keys=False),
        encoding="utf-8",
    )
    print(f"OK: imported private sample {sample_id} into {root}")
    return 0


def _validate_inputs(manifest_path: Path, thesis_source: Path, spec_source: Path) -> list[str]:
    errors: list[str] = []
    if not manifest_path.exists():
        errors.append(f"manifest is missing: {manifest_path}")
    if not thesis_source.exists():
        errors.append(f"thesis PDF is missing: {thesis_source}")
    elif thesis_source.read_bytes()[:4] != b"%PDF":
        errors.append(f"thesis file is not a PDF: {thesis_source}")
    if not spec_source.exists():
        errors.append(f"spec file is missing: {spec_source}")
    elif spec_source.suffix.lower() == ".pdf" and spec_source.read_bytes()[:4] != b"%PDF":
        errors.append(f"spec file is not a PDF: {spec_source}")
    elif spec_source.suffix.lower() != ".pdf" and not spec_source.read_text(
        encoding="utf-8", errors="ignore"
    ).strip():
        errors.append(f"spec file is empty: {spec_source}")
    return errors


def _find_entry(tiers: list, sample_id: str) -> dict | None:
    if sample_id:
        for item in tiers:
            if isinstance(item, dict) and str(item.get("id") or "") == sample_id:
                return item
        return None
    for item in tiers:
        if isinstance(item, dict) and bool(item.get("primary")):
            return item
    for item in tiers:
        if isinstance(item, dict):
            return item
    return None


def _spec_suffix(path: Path) -> str:
    suffix = path.suffix.lower()
    return suffix if suffix in {".pdf", ".md", ".markdown", ".txt"} else ".md"


def _copy_atomic(source: Path, target: Path) -> None:
    target.parent.mkdir(parents=True, exist_ok=True)
    tmp = target.with_suffix(target.suffix + ".tmp")
    shutil.copy2(source, tmp)
    tmp.replace(target)


if __name__ == "__main__":
    sys.exit(main())
