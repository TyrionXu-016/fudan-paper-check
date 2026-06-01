from __future__ import annotations

import hashlib

from mse.models import RoundIssueDiff
from schema.models import Issue


def issue_fingerprint(issue: Issue) -> str:
    page = getattr(issue, "page", None) or issue.line or 0
    rule_ref = getattr(issue, "rule_ref", None) or ""
    msg = (issue.message or "")[:50]
    key = f"{rule_ref}|{issue.section or ''}|{page}|{msg}"
    return hashlib.sha256(key.encode()).hexdigest()[:16]


def _index_issues(issues: list[Issue]) -> dict[str, Issue]:
    return {issue_fingerprint(i): i for i in issues}


def diff_rounds(
    prev_issues: list[Issue],
    curr_issues: list[Issue],
    dismissed_fps: set[str],
    *,
    base_round: int,
    current_round: int,
) -> RoundIssueDiff:
    prev_map = _index_issues(prev_issues)
    curr_map = _index_issues(curr_issues)

    fixed: list[Issue] = []
    persistent: list[Issue] = []
    new: list[Issue] = []
    dismissed: list[Issue] = []

    for fp, issue in prev_map.items():
        if fp in dismissed_fps:
            dismissed.append(issue)
        elif fp not in curr_map:
            fixed.append(issue)
        else:
            persistent.append(curr_map[fp])

    for fp, issue in curr_map.items():
        if fp not in prev_map and fp not in dismissed_fps:
            new.append(issue)

    return RoundIssueDiff(
        base_round=base_round,
        current_round=current_round,
        fixed=fixed,
        new=new,
        persistent=persistent,
        dismissed=dismissed,
    )
