from __future__ import annotations

import re

from schema.models import BlockType, PaperDocument, Span

_SENTENCE_SPLIT = re.compile(
    r"(?<=[。！？；.!?;])\s*|(?<=\n)\s*"
)


def build_spans(doc: PaperDocument) -> list[Span]:
    spans: list[Span] = []
    for block in doc.blocks:
        if block.type != BlockType.PARAGRAPH or not block.text.strip():
            continue
        text = block.text.strip()
        parts = [p.strip() for p in _SENTENCE_SPLIT.split(text) if p.strip()]
        if not parts:
            parts = [text]
        offset = 0
        for idx, part in enumerate(parts):
            start = text.find(part, offset)
            if start < 0:
                start = offset
            end = start + len(part)
            offset = end
            spans.append(
                Span(
                    id=f"{block.id}-s{idx}",
                    section_id=block.section_id,
                    block_id=block.id,
                    start_offset=start,
                    end_offset=end,
                    text=part,
                    line_start=block.line_start,
                    line_end=block.line_end,
                )
            )
    return spans
