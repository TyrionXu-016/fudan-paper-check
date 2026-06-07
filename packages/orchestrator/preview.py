from __future__ import annotations

from schema.models import Decision, DecisionAction, Issue, JobRecord, PreviewSpan, PreviewView


def _effective_span_text(
    span_id: str,
    original: str,
    issues: list[Issue],
    decisions: dict[str, Decision],
) -> tuple[str, str | None]:
    highlight: str | None = None
    text = original
    for issue in issues:
        if issue.span_id != span_id:
            continue
        decision = decisions.get(issue.id)
        if not decision or decision.action == DecisionAction.PENDING:
            continue
        if decision.action == DecisionAction.REJECT:
            continue
        if decision.action == DecisionAction.ACCEPT:
            text = issue.suggested_text or issue.suggestion or text
            highlight = "accepted"
        elif decision.action == DecisionAction.CUSTOM and decision.custom_content:
            text = decision.custom_content
            highlight = "custom"
    return text, highlight


def count_unresolved(issues: list[Issue], decisions: dict[str, Decision]) -> int:
    unresolved = 0
    for issue in issues:
        decision = decisions.get(issue.id)
        if not decision or decision.action == DecisionAction.PENDING:
            unresolved += 1
    return unresolved


def build_preview(record: JobRecord, decisions: dict[str, Decision] | None = None) -> PreviewView:
    decisions = decisions or {}
    issues = record.report.issues if record.report else []
    spans_out: list[PreviewSpan] = []

    for span in record.spans:
        text, highlight = _effective_span_text(span.id, span.text, issues, decisions)
        spans_out.append(
            PreviewSpan(
                span_id=span.id,
                section_id=span.section_id,
                text=text,
                highlight=highlight,
            )
        )

    title = ""
    if record.report:
        title = record.report.paper_title
    elif record.document:
        title = record.document.meta.title

    return PreviewView(
        task_id=record.job_id,
        paper_title=title,
        spans=spans_out,
        unresolved_count=count_unresolved(issues, decisions),
    )
