from __future__ import annotations

import re
from pathlib import Path

from schema.models import PaperDocument, Span

_PAGE_IN_IMAGE = re.compile(r"_page_(\d+)_", re.I)
_PAGE_MARKER = re.compile(r"<!--\s*page\s*:\s*(\d+)\s*-->", re.I)


class PageMapper:
    """Map document line numbers to PDF page (1-based)."""

    def __init__(self, line_to_page: dict[int, int]) -> None:
        self.line_to_page = line_to_page

    @classmethod
    def from_document(
        cls,
        doc: PaperDocument,
        *,
        maker_path: str | Path | None = None,
        mineru_path: str | Path | None = None,
    ) -> PageMapper:
        lines: list[str] = []
        if maker_path and Path(maker_path).exists():
            lines = Path(maker_path).read_text(encoding="utf-8").splitlines()
        elif mineru_path and Path(mineru_path).exists():
            lines = Path(mineru_path).read_text(encoding="utf-8").splitlines()
        else:
            for block in doc.blocks:
                if block.line_start:
                    while len(lines) < block.line_start:
                        lines.append("")
                    if block.line_start <= len(lines):
                        idx = block.line_start - 1
                        lines[idx] = block.text or lines[idx]

        mapping: dict[int, int] = {}
        current_page = 1
        for i, line in enumerate(lines, start=1):
            marker = _PAGE_MARKER.search(line)
            if marker:
                current_page = int(marker.group(1))
            img = _PAGE_IN_IMAGE.search(line)
            if img:
                current_page = int(img.group(1)) + 1
            mapping[i] = current_page

        if not mapping and lines:
            lines_per_page = 40
            for i in range(1, len(lines) + 1):
                mapping[i] = (i - 1) // lines_per_page + 1

        return cls(mapping)

    def page_for_line(self, line: int | None) -> int | None:
        if line is None:
            return None
        if line in self.line_to_page:
            return self.line_to_page[line]
        if not self.line_to_page:
            return None
        nearest = max(k for k in self.line_to_page if k <= line)
        return self.line_to_page.get(nearest)

    def page_line_label(self, page: int | None, line: int | None) -> str | None:
        if page is None:
            return None
        if line is None:
            return f"第 {page} 页"
        return f"第 {page} 页（约第 {line} 行）"

    def apply_to_spans(self, spans: list[Span]) -> list[Span]:
        updated: list[Span] = []
        for span in spans:
            page = self.page_for_line(span.line_start)
            data = span.model_dump()
            data["page"] = page
            updated.append(Span.model_validate(data))
        return updated

    def page_range_for_section(self, doc: PaperDocument, section_id: str) -> tuple[int, int]:
        section = next((s for s in doc.sections if s.id == section_id), None)
        if not section:
            return 1, 1
        pages = [
            self.page_for_line(line)
            for line in range(section.start_line, section.end_line + 1)
            if self.page_for_line(line)
        ]
        if not pages:
            return 1, 1
        return min(pages), max(pages)
