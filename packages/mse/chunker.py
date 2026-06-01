from __future__ import annotations

from dataclasses import dataclass

from schema.models import PaperDocument, Section


@dataclass
class SectionChunk:
    section_id: str
    title: str
    text: str
    start_line: int
    end_line: int
    page_start: int
    page_end: int


def iter_section_chunks(
    doc: PaperDocument,
    *,
    page_start: int = 1,
    page_end: int = 1,
    max_chars: int = 6000,
) -> list[SectionChunk]:
    """Split document into section-level chunks for LLM review."""
    chunks: list[SectionChunk] = []
    for section in doc.sections:
        body = _section_text(doc, section)
        if not body.strip():
            continue
        if len(body) <= max_chars:
            chunks.append(
                SectionChunk(
                    section_id=section.id,
                    title=section.title,
                    text=body,
                    start_line=section.start_line,
                    end_line=section.end_line,
                    page_start=page_start,
                    page_end=page_end,
                )
            )
            continue
        parts = _split_text(body, max_chars)
        for idx, part in enumerate(parts):
            chunks.append(
                SectionChunk(
                    section_id=f"{section.id}#{idx}",
                    title=section.title,
                    text=part,
                    start_line=section.start_line,
                    end_line=section.end_line,
                    page_start=page_start,
                    page_end=page_end,
                )
            )
    return chunks


def _section_text(doc: PaperDocument, section: Section) -> str:
    lines: list[str] = []
    for block in doc.blocks:
        if block.section_id == section.id and block.text:
            lines.append(block.text.strip())
    return "\n\n".join(lines)


def _split_text(text: str, max_chars: int) -> list[str]:
    if len(text) <= max_chars:
        return [text]
    parts: list[str] = []
    start = 0
    while start < len(text):
        end = min(start + max_chars, len(text))
        if end < len(text):
            cut = text.rfind("\n\n", start, end)
            if cut > start:
                end = cut
        parts.append(text[start:end].strip())
        start = end
    return [p for p in parts if p]
