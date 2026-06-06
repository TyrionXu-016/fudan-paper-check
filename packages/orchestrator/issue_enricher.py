from __future__ import annotations

import uuid

from schema.models import CheckCategory, Issue, IssueType, PaperDocument, Span


_CATEGORY_TO_ISSUE_TYPE: dict[CheckCategory, IssueType] = {
    CheckCategory.STRUCTURE: IssueType.FORMAT,
    CheckCategory.FORMAT: IssueType.FORMAT,
    CheckCategory.REFERENCE: IssueType.REFERENCE,
    CheckCategory.CONSISTENCY: IssueType.LOGIC_CONTRADICTION,
}


def _find_span_for_issue(issue: Issue, spans: list[Span], doc: PaperDocument) -> Span | None:
    if issue.evidence:
        for span in spans:
            if issue.evidence in span.text or span.text in issue.evidence:
                return span
    if issue.line is not None:
        for span in spans:
            if span.line_start is not None and span.line_end is not None:
                if span.line_start <= issue.line <= span.line_end:
                    return span
    if issue.section:
        section_ids = {s.id for s in doc.sections if s.kind.value == issue.section}
        for span in spans:
            if span.section_id in section_ids:
                return span
    return None


def enrich_issues(
    issues: list[Issue],
    doc: PaperDocument,
    spans: list[Span],
) -> list[Issue]:
    enriched: list[Issue] = []
    for issue in issues:
        data = issue.model_dump()
        if not data.get("id"):
            data["id"] = str(uuid.uuid4())
        if not data.get("issue_type"):
            data["issue_type"] = _CATEGORY_TO_ISSUE_TYPE.get(
                issue.category, IssueType.FORMAT
            )
        span = _find_span_for_issue(issue, spans, doc)
        if span:
            data["span_id"] = span.id
            if not data.get("original_text"):
                data["original_text"] = span.text
        if not data.get("original_text") and issue.evidence:
            data["original_text"] = issue.evidence[:500]
        if not data.get("suggested_text") and issue.suggestion:
            data["suggested_text"] = issue.suggestion
        enriched.append(Issue.model_validate(data))
    return enriched
