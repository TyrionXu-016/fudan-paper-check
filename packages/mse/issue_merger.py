from __future__ import annotations

from schema.models import Issue


def issue_fingerprint(issue: Issue) -> str:
    parts = [
        issue.code or "",
        issue.category.value if issue.category else "",
        (issue.original_text or "")[:120],
        str(issue.line or ""),
        str(issue.page or ""),
        issue.section or "",
    ]
    return "|".join(parts)


def merge_issues(*issue_lists: list[Issue]) -> list[Issue]:
    """Deduplicate issues; keep higher severity on conflict."""
    by_fp: dict[str, Issue] = {}
    severity_rank = {"error": 3, "warning": 2, "info": 1}

    for issues in issue_lists:
        for issue in issues:
            fp = issue_fingerprint(issue)
            existing = by_fp.get(fp)
            if not existing:
                by_fp[fp] = issue
                continue
            cur = severity_rank.get(issue.severity.value, 0)
            old = severity_rank.get(existing.severity.value, 0)
            if cur > old:
                by_fp[fp] = issue
    return list(by_fp.values())
