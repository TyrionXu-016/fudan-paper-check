from __future__ import annotations

import io

from pypdf import PdfReader

from schema.models import CheckCategory, Issue, IssueSeverity, IssueType
from mse.export import export_round_markdown, export_round_pdf_bytes


def _issue(**kwargs) -> Issue:
    return Issue(
        code=kwargs.get("code", "T"),
        category=kwargs.get("category", CheckCategory.FORMAT),
        severity=kwargs.get("severity", IssueSeverity.WARNING),
        message=kwargs.get("message", "test"),
        page=kwargs.get("page"),
        page_line=kwargs.get("page_line"),
        revision_hint=kwargs.get("revision_hint", ""),
        issue_type=IssueType.FORMAT,
    )


def test_export_markdown_groups_by_page():
    issues = [
        _issue(code="A", page=2, message="页2问题", revision_hint="改2"),
        _issue(code="B", page=1, message="页1问题"),
    ]
    md = export_round_markdown(project_title="测试论文", round_number=1, issues=issues)
    assert "第 1 页" in md
    assert "第 2 页" in md
    assert "页1问题" in md
    assert "改2" in md


def test_export_pdf_non_empty():
    issues = [_issue(page=3, message="摘要格式问题", revision_hint="补充关键词")]
    pdf = export_round_pdf_bytes(
        project_title="测试",
        round_number=2,
        issues=issues,
        gate_passed=False,
        gate_reason="warnings",
    )
    assert pdf[:4] == b"%PDF"


def test_export_pdf_contains_page_anchors_and_rule_refs():
    issues = [
        _issue(
            code="ANCHOR",
            page=3,
            message="Anchor issue",
            revision_hint="Use a stronger revision",
        )
    ]
    issues[0].rule_ref = "rule-1"
    issues[0].original_text = "Original quoted text"

    pdf = export_round_pdf_bytes(
        project_title="Anchor Report",
        round_number=1,
        issues=issues,
    )

    text = "\n".join(page.extract_text() or "" for page in PdfReader(io.BytesIO(pdf)).pages)
    assert "Issue Anchor: page-3" in text
    assert "rule-1" in text
    assert "Original quoted text" in text
