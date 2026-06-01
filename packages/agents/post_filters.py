from __future__ import annotations

from schema.models import CheckCategory, Issue, IssueSeverity, IssueType


def apply_mse_post_filters(issues: list[Issue], *, max_page: int = 500) -> list[Issue]:
    out: list[Issue] = []
    for issue in issues:
        if issue.page is not None and (issue.page < 1 or issue.page > max_page):
            issue.page = None
        if issue.severity == IssueSeverity.ERROR and not issue.rule_ref:
            if issue.category == CheckCategory.CONSISTENCY and issue.issue_type == IssueType.LLM:
                issue.severity = IssueSeverity.WARNING
                issue.message = f"[需人工确认] {issue.message}"
        if not issue.revision_hint and issue.suggested_text:
            issue.revision_hint = issue.suggested_text[:200]
        out.append(issue)
    return out
