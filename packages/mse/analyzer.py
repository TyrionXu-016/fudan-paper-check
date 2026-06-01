from __future__ import annotations

from pathlib import Path

from agents.mse_review_agent import MseReviewAgent
from mse.chunker import SectionChunk, _section_text, _split_text
from mse.figure_table_checker import FigureTableChecker
from mse.issue_merger import merge_issues
from orchestrator.issue_enricher import enrich_issues
from parser.page_mapper import PageMapper
from parser.span_builder import build_spans
from schema.models import Issue, PaperDocument, Span


def _section_chunks(doc: PaperDocument, mapper: PageMapper) -> list[SectionChunk]:
    chunks: list[SectionChunk] = []
    for section in doc.sections:
        body = _section_text(doc, section)
        if not body.strip():
            continue
        p_start, p_end = mapper.page_range_for_section(doc, section.id)
        parts = _split_text(body, 6000) if len(body) > 6000 else [body]
        for idx, part in enumerate(parts):
            chunks.append(
                SectionChunk(
                    section_id=f"{section.id}#{idx}" if len(parts) > 1 else section.id,
                    title=section.title,
                    text=part,
                    start_line=section.start_line,
                    end_line=section.end_line,
                    page_start=p_start,
                    page_end=p_end,
                )
            )
    return chunks


def run_mse_analysis(
    doc: PaperDocument,
    base_issues: list[Issue],
    *,
    project_id: str,
    journal_profile: str = "generic",
    maker_path: str | Path | None = None,
    mineru_path: str | Path | None = None,
    spans: list[Span] | None = None,
    llm_sections: int | None = None,
) -> tuple[list[Issue], list[Span]]:
    """M1 analyzer: page mapping, figure checks, per-section LLM review, merge."""
    mapper = PageMapper.from_document(doc, maker_path=maker_path, mineru_path=mineru_path)
    spans = mapper.apply_to_spans(spans or build_spans(doc))

    figure_issues = FigureTableChecker().check(doc, page_for_line=mapper.page_for_line)

    agent = MseReviewAgent()
    llm_issues: list[Issue] = []
    chunks = _section_chunks(doc, mapper)
    limit = llm_sections if llm_sections is not None else len(chunks)
    for chunk in chunks[:limit]:
        llm_issues.extend(
            agent.review_chunk(chunk, project_id=project_id, journal_profile=journal_profile)
        )

    merged = merge_issues(base_issues, figure_issues, llm_issues)
    enriched = enrich_issues(merged, doc, spans, page_mapper=mapper)
    return enriched, spans
