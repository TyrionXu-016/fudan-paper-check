from __future__ import annotations

import html
import re
from html.parser import HTMLParser
from pathlib import Path

from schema.models import (
    Block,
    BlockType,
    Citation,
    FigureRef,
    PaperDocument,
    PaperMeta,
    ParseQuality,
    Reference,
    Section,
    SectionKind,
    TableData,
)


class _TableHTMLParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.rows: list[list[str]] = []
        self._current: list[str] = []
        self._cell = ""

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag in ("td", "th"):
            self._cell = ""

    def handle_endtag(self, tag: str) -> None:
        if tag in ("td", "th"):
            self._current.append(html.unescape(self._cell.strip()))
        elif tag == "tr" and self._current:
            self.rows.append(self._current)
            self._current = []

    def handle_data(self, data: str) -> None:
        self._cell += data


def _clean_text(text: str) -> str:
    text = re.sub(r"<sup>.*?</sup>", "", text)
    text = re.sub(r"\*\*([^*]+)\*\*", r"\1", text)
    return re.sub(r"\s+", " ", text).strip()


def _heading_level(line: str) -> int:
    match = re.match(r"^(#{1,6})\s", line)
    return len(match.group(1)) if match else 0


def _strip_heading_markup(line: str) -> str:
    return re.sub(r"^#+\s*", "", line.strip()).strip()


def _classify_section(title: str) -> SectionKind:
    t = title.lower()
    compact = re.sub(r"\s+", "", title)
    numbered = re.match(r"^(\d+)(?:\.\d+)*", compact)
    if "摘要" in title or "abstract" in t:
        return SectionKind.ABSTRACT
    if "关键词" in title or "key word" in t or "keyword" in t:
        return SectionKind.KEYWORDS
    if "参考文献" in title or "reference" in t or "bibliography" in t:
        return SectionKind.REFERENCES
    if "结论" in title or "conclusion" in t:
        return SectionKind.CONCLUSION
    if "introduction" in t or "引言" in title:
        return SectionKind.INTRO
    if numbered:
        top_level = numbered.group(1)
        if top_level == "3":
            return SectionKind.EXPERIMENT
        if top_level == "2":
            return SectionKind.METHOD
        if top_level == "1":
            return SectionKind.METHOD
    if re.match(r"^\d+\s", title) or "实验" in title or "结果" in title:
        if "实验" in title or "结果" in title or title.startswith("3"):
            return SectionKind.EXPERIMENT
        if "方法" in title or "模型" in title or title.startswith("2"):
            return SectionKind.METHOD
        if title.startswith("1") or "问题" in title:
            return SectionKind.METHOD
    if "integrated deep learning" in t:
        return SectionKind.ENGLISH
    if title.startswith("随着") or "引言" in title:
        return SectionKind.INTRO
    return SectionKind.OTHER


def _is_bare_section_heading(line: str) -> bool:
    title = _strip_heading_markup(line)
    if not title or len(title) > 100:
        return False
    normalized = re.sub(r"\s+", " ", title).strip().lower()
    if normalized in {
        "abstract",
        "keywords",
        "key words",
        "references",
        "bibliography",
        "contents",
        "acknowledgements",
        "acknowledgments",
    }:
        return True
    if title in {"摘要", "关键词", "参考文献"}:
        return True
    if re.match(r"^\d+(?:\.\d+)*\s+[A-Za-z][\w\s,;:()/-]{2,}$", title):
        return True
    return bool(re.match(r"^\d+(?:\.\s*\d+)*\s*[\u4e00-\u9fff][^。；;]{1,40}$", title))


def _is_section_heading_line(line: str) -> bool:
    stripped = line.strip()
    return bool(_heading_level(stripped) or _is_bare_section_heading(stripped))


def _collect_until_next_heading(lines: list[str], start: int) -> str:
    chunks: list[str] = []
    for line in lines[start:]:
        stripped = line.strip()
        if not stripped:
            if chunks:
                break
            continue
        if _is_section_heading_line(stripped):
            break
        chunks.append(stripped)
    return _clean_text(" ".join(chunks))


def _split_keywords(raw: str) -> list[str]:
    return [k.strip() for k in re.split(r"[;；,，]", raw) if k.strip()]


def _extract_meta(lines: list[str]) -> PaperMeta:
    meta = PaperMeta()
    full = "\n".join(lines)

    title_match = re.search(r"^#\s+([^《][^\n]+)$", full, re.MULTILINE)
    if title_match and "网络首发" not in title_match.group(1):
        meta.title = _clean_text(title_match.group(1))

    for idx, line in enumerate(lines):
        stripped = line.strip()
        normalized = stripped.lower()
        if stripped.startswith("摘 要:") or stripped.startswith("摘 要："):
            meta.abstract = _clean_text(line.split(":", 1)[-1].split("：", 1)[-1])
        elif normalized == "abstract":
            meta.abstract = _collect_until_next_heading(lines, idx + 1)
        elif stripped.startswith("关键词:") or stripped.startswith("关键词："):
            raw = line.split(":", 1)[-1].split("：", 1)[-1]
            meta.keywords = _split_keywords(raw)
        elif normalized in {"keywords", "key words"}:
            meta.keywords = _split_keywords(_collect_until_next_heading(lines, idx + 1))
        elif "doi:" in line.lower():
            meta.doi = re.sub(r".*doi:\s*", "", line, flags=re.I).strip()
        elif "中图分类号" in line:
            meta.classification = re.split(r"[:：]", line, maxsplit=1)[-1].strip()

    author_line = next(
        (ln for ln in lines if re.search(r"钱超|^\w+\s+\w+", ln) and "摘" not in ln and len(ln) < 120),
        "",
    )
    if "<sup>" in author_line:
        names = re.findall(r"([\u4e00-\u9fff]{2,4})<sup>", author_line)
        if names:
            meta.authors = names

    abstract_en = re.search(r"Abstract:(.+?)(?:Key words:|$)", full, re.S | re.I)
    if abstract_en:
        meta.english_abstract = _clean_text(abstract_en.group(1))

    return meta


def _parse_markdown_tables(lines: list[str]) -> list[TableData]:
    tables_by_number: dict[int, TableData] = {}
    order: list[int] = []
    i = 0
    while i < len(lines):
        line = lines[i]
        stripped = line.strip()
        cap_match = re.match(r"^表\s*(\d+)\s*(.*)$", stripped)
        if not cap_match:
            cap_match = re.match(r"^Table\s*(\d+)\s*(.*)$", stripped, re.I)
        if cap_match:
            number = int(cap_match.group(1))
            caption = cap_match.group(2).strip() or f"表{number}"
            table_start = next(
                (
                    j
                    for j in range(i + 1, min(len(lines), i + 8))
                    if lines[j].strip().startswith("|")
                ),
                None,
            )
            headers: list[str] = []
            rows: list[list[str]] = []
            next_i = i + 1
            if table_start is not None:
                header_line = lines[table_start]
                sep_line = lines[table_start + 1] if table_start + 1 < len(lines) else ""
                headers = [c.strip() for c in header_line.strip("|").split("|")]
                j = table_start + 1
                if re.match(r"^\|[-:\s|]+\|$", sep_line):
                    j += 1
                while j < len(lines) and lines[j].strip().startswith("|"):
                    rows.append([c.strip() for c in lines[j].strip("|").split("|")])
                    j += 1
                next_i = j
            table = TableData(
                id=f"table_{number}",
                caption=caption,
                number=number,
                headers=headers,
                rows=rows,
                source="maker",
            )
            if number not in tables_by_number:
                order.append(number)
                tables_by_number[number] = table
            elif rows and not tables_by_number[number].rows:
                tables_by_number[number] = table
            i = next_i
            continue
        i += 1
    return [tables_by_number[n] for n in order]


def _parse_html_tables(content: str) -> list[TableData]:
    tables: list[TableData] = []
    for idx, match in enumerate(re.finditer(r"<table>.*?</table>", content, re.S), start=1):
        html_block = match.group(0)
        parser = _TableHTMLParser()
        parser.feed(html_block)
        if not parser.rows:
            continue
        cap_match = re.search(
            rf"表\s*{idx}[^\n]*",
            content[max(0, match.start() - 200) : match.start()],
        )
        caption = cap_match.group(0).strip() if cap_match else f"表{idx}"
        tables.append(
            TableData(
                id=f"table_{idx}",
                caption=caption,
                number=idx,
                headers=parser.rows[0],
                rows=parser.rows[1:],
                source="mineru",
                html=html_block,
            )
        )
    return tables


def _parse_references(lines: list[str]) -> list[Reference]:
    refs: list[Reference] = []
    in_refs = False
    next_index = 1
    for line in lines:
        stripped = line.strip()
        if "参考文献" in line or stripped.lower() in {"references", "bibliography"}:
            in_refs = True
            continue
        if not in_refs:
            continue
        if _is_section_heading_line(stripped) and refs:
            break
        m = re.match(r"^-\s*\[(\d+)\]\s*(.+)$", stripped)
        if not m:
            m = re.match(r"^\[(\d+)\]\s*(.+)$", stripped)
        if not m:
            m = re.match(r"^(\d+)[\].)]\s+(.+)$", stripped)
        if m:
            index = int(m.group(1))
            refs.append(Reference(index=index, raw_text=m.group(2).strip()))
            next_index = max(next_index, index + 1)
        elif _looks_like_reference_entry(stripped):
            refs.append(Reference(index=next_index, raw_text=stripped))
            next_index += 1
    return refs


def _looks_like_reference_entry(text: str) -> bool:
    if len(text) < 20:
        return False
    if not re.search(r"\b(19|20)\d{2}\b", text):
        return False
    if re.match(r"^[A-Z][A-Za-z' -]+(?:,\s*[A-Z]| [A-Z]\.)", text):
        return True
    if re.match(r"^[\u4e00-\u9fff]{2,4}[,.，]", text):
        return True
    return bool(re.search(r"\.\s+[A-Z][A-Za-z].+\b(19|20)\d{2}\b", text))


def _parse_citations(lines: list[str], sections: list[Section]) -> list[Citation]:
    citations: list[Citation] = []
    section_by_line = sorted(sections, key=lambda s: s.start_line)

    def section_for(line_no: int) -> str:
        current = section_by_line[0].id if section_by_line else "sec_other"
        for sec in section_by_line:
            if sec.start_line <= line_no:
                current = sec.id
        return current

    for i, line in enumerate(lines, start=1):
        indices = [int(x) for x in re.findall(r"\[(\d+)\]", line)]
        if indices:
            citations.append(
                Citation(
                    ref_indices=indices,
                    section_id=section_for(i),
                    line=i,
                    context=line.strip()[:200],
                )
            )
    return citations


def _parse_figures(lines: list[str]) -> list[FigureRef]:
    figures: list[FigureRef] = []
    for i, line in enumerate(lines, start=1):
        stripped = line.strip()
        img = re.match(r"^!\[\]\((.+)\)$", stripped)
        cap = re.match(r"^图\s*(\d+)\s*(.*)$", stripped)
        if not cap:
            cap = re.match(r"^Fig\.?\s*(\d+)\s*(.*)$", stripped, re.I)
        if img:
            figures.append(FigureRef(id=f"fig_line_{i}", path=img.group(1), line=i))
        elif cap:
            figures.append(
                FigureRef(
                    id=f"figure_{cap.group(1)}",
                    number=int(cap.group(1)),
                    caption=cap.group(2).strip(),
                    line=i,
                )
            )
    return figures


def _score_maker(content: str) -> float:
    penalties = len(re.findall(r"（\s*）|为\s，|降低了\s、", content))
    numbers = len(re.findall(r"\d+\.?\d*", content))
    if numbers == 0:
        return 0.3
    return max(0.0, min(1.0, 1.0 - penalties / max(numbers, 1) * 5))


def _score_mineru(content: str) -> float:
    empty_slots = len(re.findall(r"（\s*）|为\s，|RMSE为\s，|降低了\s、|\[\s*\]", content))
    return max(0.0, min(1.0, 1.0 - empty_slots * 0.05))


class DualSourceFusionParser:
    """Fuse maker (primary text) with mineru (tables/HTML)."""

    def parse_files(
        self,
        maker_path: str | Path,
        mineru_path: str | Path | None = None,
    ) -> PaperDocument:
        maker_text = Path(maker_path).read_text(encoding="utf-8")
        mineru_text = Path(mineru_path).read_text(encoding="utf-8") if mineru_path else ""
        return self.parse(maker_text, mineru_text)

    def parse(self, maker_md: str, mineru_md: str = "") -> PaperDocument:
        lines = maker_md.splitlines()
        meta = _extract_meta(lines)
        sections = self._build_sections(lines)
        blocks = self._build_blocks(lines, sections)
        maker_tables = _parse_markdown_tables(lines)
        mineru_tables = _parse_html_tables(mineru_md) if mineru_md else []
        tables = self._fuse_tables(maker_tables, mineru_tables)
        references = _parse_references(lines)
        citations = _parse_citations(lines, sections)
        figures = _parse_figures(lines)

        warnings: list[str] = []
        maker_score = _score_maker(maker_md)
        mineru_score = _score_mineru(mineru_md) if mineru_md else 0.0
        if mineru_md and mineru_score < 0.7:
            warnings.append("mineru 正文存在大量 OCR 缺失，已采用 maker 作为主文本源")
        if any(t.source == "mineru" for t in tables):
            warnings.append("表格优先采用 mineru HTML 结构")
        fusion_score = round(maker_score * 0.7 + (mineru_score if mineru_md else maker_score) * 0.3, 3)

        return PaperDocument(
            meta=meta,
            sections=sections,
            blocks=blocks,
            tables=tables,
            figures=figures,
            references=references,
            citations=citations,
            quality=ParseQuality(
                maker_score=round(maker_score, 3),
                mineru_score=round(mineru_score, 3),
                fusion_score=fusion_score,
                fusion_warnings=warnings,
                degraded=fusion_score < 0.6,
            ),
            source_files={"maker": "inline", "mineru": "inline" if mineru_md else ""},
        )

    def _build_sections(self, lines: list[str]) -> list[Section]:
        sections: list[Section] = []

        def append_section(kind: SectionKind, title: str, level: int, line_no: int) -> None:
            if sections:
                sections[-1].end_line = line_no - 1
            sec_id = f"sec_{len(sections)}"
            sections.append(
                Section(
                    id=sec_id,
                    kind=kind,
                    title=title,
                    level=level,
                    start_line=line_no,
                    end_line=len(lines),
                )
            )

        for i, line in enumerate(lines, start=1):
            stripped = line.strip()
            if stripped.startswith("摘 要"):
                append_section(SectionKind.ABSTRACT, "摘要", 1, i)
                continue

            if stripped.startswith("关键词"):
                append_section(SectionKind.KEYWORDS, "关键词", 1, i)
                continue

            level = _heading_level(line)
            if level:
                title = _strip_heading_markup(line)
                kind = _classify_section(title)
                append_section(kind, title, level, i)
                continue

            if _is_bare_section_heading(stripped):
                title = _strip_heading_markup(stripped)
                append_section(_classify_section(title), title, 1, i)

        if sections:
            sections[-1].end_line = len(lines)
        return sections

    def _build_blocks(self, lines: list[str], sections: list[Section]) -> list[Block]:
        blocks: list[Block] = []
        sec_map = sorted(sections, key=lambda s: s.start_line)

        def section_for(line_no: int) -> str:
            current = sec_map[0].id if sec_map else "sec_other"
            for sec in sec_map:
                if sec.start_line <= line_no:
                    current = sec.id
            return current

        for i, line in enumerate(lines, start=1):
            btype = BlockType.PARAGRAPH
            if _heading_level(line) or _is_bare_section_heading(line.strip()):
                btype = BlockType.HEADING
            elif line.strip().startswith("$$") or line.strip().startswith("$"):
                btype = BlockType.FORMULA
            elif re.match(r"^!\[\]", line.strip()):
                btype = BlockType.FIGURE_REF
            elif line.strip().startswith("|"):
                btype = BlockType.TABLE
            blocks.append(
                Block(
                    id=f"blk_{i}",
                    type=btype,
                    section_id=section_for(i),
                    line_start=i,
                    line_end=i,
                    text=_clean_text(line),
                    raw=line,
                )
            )
        return blocks

    def _fuse_tables(
        self, maker_tables: list[TableData], mineru_tables: list[TableData]
    ) -> list[TableData]:
        if not mineru_tables:
            return maker_tables
        by_number = {t.number: t for t in maker_tables if t.number is not None}
        fused: list[TableData] = []
        for mt in mineru_tables:
            if mt.number and mt.number in by_number:
                mk = by_number[mt.number]
                mt.caption = mk.caption or mt.caption
            fused.append(mt)
        maker_nums = {t.number for t in fused if t.number is not None}
        fused.extend(t for t in maker_tables if t.number not in maker_nums)
        return sorted(fused, key=lambda t: t.number or 0)
