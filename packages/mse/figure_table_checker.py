from __future__ import annotations

from pathlib import Path

import yaml

from schema.models import (
    CheckCategory,
    Issue,
    IssueSeverity,
    IssueType,
    PaperDocument,
)

_ROOT = Path(__file__).resolve().parents[2]
_RULES_PATH = _ROOT / "config" / "mse" / "figure_rules.yaml"


class FigureTableChecker:
    """Rule-based figure/table caption and reference checks."""

    def __init__(self, rules_path: Path | None = None) -> None:
        path = rules_path or _RULES_PATH
        self.rules = yaml.safe_load(path.read_text(encoding="utf-8")) if path.exists() else {}

    def check(self, doc: PaperDocument, *, page_for_line=None) -> list[Issue]:
        issues: list[Issue] = []
        body = "\n".join(b.text for b in doc.blocks if b.text)
        figures = doc.figures or []

        numbers = sorted({f.number for f in figures if f.number is not None})
        if self.rules.get("sequential_numbers") and numbers:
            expected = list(range(1, max(numbers) + 1))
            missing = [n for n in expected if n not in numbers]
            for n in missing:
                issues.append(
                    Issue(
                        code="MSE_FIG_SEQUENCE",
                        category=CheckCategory.FORMAT,
                        severity=IssueSeverity.WARNING,
                        message=f"图序号不连续，缺少图 {n}",
                        issue_type=IssueType.FORMAT,
                    )
                )

        for fig in figures:
            page = fig.page
            if page is None and fig.line and page_for_line:
                page = page_for_line(fig.line)

            if self.rules.get("require_caption") and fig.number and not (fig.caption or "").strip():
                issues.append(
                    Issue(
                        code="MSE_FIG_CAPTION",
                        category=CheckCategory.FORMAT,
                        severity=IssueSeverity.WARNING,
                        message=f"图 {fig.number} 缺少题注",
                        line=fig.line,
                        page=page,
                        issue_type=IssueType.FORMAT,
                    )
                )

            if self.rules.get("require_body_reference") and fig.number is not None:
                refs = (f"图{fig.number}", f"图 {fig.number}")
                if not any(r in body for r in refs):
                    issues.append(
                        Issue(
                            code="MSE_FIG_UNREFERENCED",
                            category=CheckCategory.FORMAT,
                            severity=IssueSeverity.INFO,
                            message=f"正文可能未引用图 {fig.number}",
                            line=fig.line,
                            page=page,
                            issue_type=IssueType.FORMAT,
                        )
                    )

        return issues
