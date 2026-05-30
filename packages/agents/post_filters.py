from __future__ import annotations

import re

from schema.models import Issue


def apply_typo_grammar_filters(issues: list[Issue], span_text: str) -> list[Issue]:
    """
    Validates the generated issues.
    """
    valid_issues = []
    for issue in issues:
        # 1. Original text must be a substring of the span
        if issue.original_text not in span_text:
            continue

        # 2. Check if numbers are unchanged
        orig_nums = sorted(re.findall(r"\d+(?:\.\d+)?", issue.original_text))
        sugg_nums = sorted(re.findall(r"\d+(?:\.\d+)?", issue.suggested_text))
        if orig_nums != sugg_nums:
            continue

        # 3. Check reference markers [1], [2,3]
        orig_refs = sorted(re.findall(r"\[\d+(?:,\s*\d+)*\]", issue.original_text))
        sugg_refs = sorted(re.findall(r"\[\d+(?:,\s*\d+)*\]", issue.suggested_text))
        if orig_refs != sugg_refs:
            continue

        # 4. Whitelist check (e.g. ARIMA) - simplistic placeholder
        whitelist = ["ARIMA", "CNN", "RNN", "LSTM"]
        failed_whitelist = False
        for w in whitelist:
            if w in issue.original_text and w not in issue.suggested_text:
                failed_whitelist = True
                break
        if failed_whitelist:
            continue

        valid_issues.append(issue)
        
    return valid_issues
