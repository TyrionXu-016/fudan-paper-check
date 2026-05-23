from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path

import yaml

from schema.models import CheckCategory, Issue, PaperDocument


class BaseChecker(ABC):
    category: CheckCategory

    @abstractmethod
    def check(self, doc: PaperDocument) -> list[Issue]:
        raise NotImplementedError


def load_journal_profile(name: str) -> dict:
    root = Path(__file__).resolve().parents[2]
    path = root / "config" / "journals" / f"{name}.yaml"
    if not path.exists():
        path = root / "config" / "journals" / "generic.yaml"
    with path.open(encoding="utf-8") as f:
        return yaml.safe_load(f)


def section_text(doc: PaperDocument, kind: str) -> str:
    from schema.models import SectionKind

    try:
        sk = SectionKind(kind)
    except ValueError:
        return ""
    lines: list[str] = []
    for sec in doc.sections:
        if sec.kind == sk:
            for blk in doc.blocks:
                if blk.section_id == sec.id and blk.type.value != "heading":
                    lines.append(blk.text)
    if kind == "abstract" and doc.meta.abstract:
        lines.insert(0, doc.meta.abstract)
    return "\n".join(lines)
