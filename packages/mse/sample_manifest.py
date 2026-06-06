from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml


@dataclass(frozen=True)
class SampleEntry:
    id: str
    tier: str
    primary: bool
    thesis_pdf: str = ""
    spec_file: str = ""
    school: str = ""
    subfield: str = ""


@dataclass
class SampleManifestValidation:
    manifest_path: Path
    entries: list[SampleEntry] = field(default_factory=list)
    missing: list[str] = field(default_factory=list)
    invalid: list[str] = field(default_factory=list)

    def _entry_has_issue(self, entry: SampleEntry) -> bool:
        prefixes = {item.split(" ", 1)[0] for item in self.missing + self.invalid}
        return entry.id in prefixes

    @property
    def ready_primary_entries(self) -> list[SampleEntry]:
        return [
            entry
            for entry in self.entries
            if entry.primary and entry.thesis_pdf and entry.spec_file and not self._entry_has_issue(entry)
        ]

    @property
    def primary_ready_count(self) -> int:
        return len(self.ready_primary_entries)

    @property
    def ready(self) -> bool:
        return not self.missing and not self.invalid and self.primary_ready_count > 0


def load_sample_manifest(path: Path) -> list[SampleEntry]:
    raw = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    entries: list[SampleEntry] = []
    for item in raw.get("tiers") or []:
        if not isinstance(item, dict):
            continue
        entries.append(
            SampleEntry(
                id=str(item.get("id") or ""),
                tier=str(item.get("tier") or ""),
                primary=bool(item.get("primary")),
                thesis_pdf=str(item.get("thesis_pdf") or ""),
                spec_file=str(item.get("spec_file") or item.get("spec") or ""),
                school=str(item.get("school") or ""),
                subfield=str(item.get("subfield") or ""),
            )
        )
    return entries


def validate_sample_manifest(
    path: str | Path,
    *,
    require_primary: bool = False,
) -> SampleManifestValidation:
    manifest_path = Path(path)
    result = SampleManifestValidation(manifest_path=manifest_path)
    if not manifest_path.exists():
        result.missing.append(f"manifest {manifest_path}")
        return result

    root = manifest_path.parent
    result.entries = load_sample_manifest(manifest_path)
    for entry in result.entries:
        if require_primary and not entry.primary:
            continue
        if not entry.thesis_pdf or not entry.spec_file:
            if require_primary or entry.primary:
                if not entry.thesis_pdf:
                    result.missing.append(f"{entry.id} thesis_pdf <unset>")
                if not entry.spec_file:
                    result.missing.append(f"{entry.id} spec_file <unset>")
            continue
        _check_file(root, entry, "thesis_pdf", entry.thesis_pdf, result, pdf=True)
        _check_file(root, entry, "spec_file", entry.spec_file, result, pdf=entry.spec_file.lower().endswith(".pdf"))
    return result


def _check_file(
    root: Path,
    entry: SampleEntry,
    field_name: str,
    rel_path: str,
    result: SampleManifestValidation,
    *,
    pdf: bool,
) -> None:
    path = root / rel_path
    if not path.exists():
        result.missing.append(f"{entry.id} {field_name} {rel_path}")
        return
    if pdf and path.read_bytes()[:4] != b"%PDF":
        result.invalid.append(f"{entry.id} {field_name} {rel_path} is not a PDF")
        return
    if not pdf and path.stat().st_size == 0:
        result.invalid.append(f"{entry.id} {field_name} {rel_path} is empty")
