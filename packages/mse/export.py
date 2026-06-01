from __future__ import annotations

import io
from collections import defaultdict

from schema.models import Issue, IssueSeverity


def export_round_markdown(
    *,
    project_title: str,
    round_number: int,
    issues: list[Issue],
    gate_reason: str = "",
    gate_passed: bool | None = None,
) -> str:
    lines = [
        f"# {project_title} — 第 {round_number} 轮审查意见",
        "",
    ]
    if gate_passed is not None:
        status = "通过" if gate_passed else "未通过"
        lines.append(f"**格式门禁**：{status}（{gate_reason or '—'}）")
        lines.append("")

    errors = sum(1 for i in issues if i.severity == IssueSeverity.ERROR)
    warnings = sum(1 for i in issues if i.severity == IssueSeverity.WARNING)
    infos = sum(1 for i in issues if i.severity == IssueSeverity.INFO)
    lines.append(f"共 {len(issues)} 项：{errors} 错误 / {warnings} 警告 / {infos} 提示")
    lines.append("")

    if not issues:
        lines.append("未发现问题。")
        return "\n".join(lines) + "\n"

    by_page: dict[int, list[Issue]] = defaultdict(list)
    for issue in issues:
        by_page[int(issue.page or 0)].append(issue)

    for page in sorted(by_page.keys()):
        if page > 0:
            lines.append(f"## 第 {page} 页")
        else:
            lines.append("## 未定位页码")
        lines.append("")
        for issue in by_page[page]:
            page_label = getattr(issue, "page_line", None) or (
                f"第 {issue.page} 页" if issue.page else ""
            )
            hint = getattr(issue, "revision_hint", None) or issue.suggestion or ""
            lines.append(f"### [{issue.severity.value}] {issue.code}")
            if page_label:
                lines.append(f"- **页码**：{page_label}")
            lines.append(f"- **说明**：{issue.message}")
            if hint:
                lines.append(f"- **修改建议**：{hint}")
            if getattr(issue, "rule_ref", None):
                lines.append(f"- **规范引用**：{issue.rule_ref}")
            if issue.original_text:
                lines.append(f"- **原文**：{issue.original_text[:200]}")
            lines.append("")
    return "\n".join(lines).strip() + "\n"


def export_round_pdf_bytes(
    *,
    project_title: str,
    round_number: int,
    issues: list[Issue],
    gate_reason: str = "",
    gate_passed: bool | None = None,
) -> bytes:
    try:
        from reportlab.lib import colors
        from reportlab.lib.pagesizes import A4
        from reportlab.lib.units import mm
        from reportlab.pdfbase import pdfmetrics
        from reportlab.pdfbase.cidfonts import UnicodeCIDFont
        from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle
        from reportlab.lib.styles import ParagraphStyle
    except ImportError as exc:
        raise RuntimeError("reportlab is required for pdf export") from exc

    font_name = "STSong-Light"
    try:
        pdfmetrics.registerFont(UnicodeCIDFont(font_name))
    except Exception:
        font_name = "Helvetica"

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, leftMargin=18 * mm, rightMargin=18 * mm)
    title_style = ParagraphStyle("title", fontName=font_name, fontSize=14, leading=18)
    body_style = ParagraphStyle("body", fontName=font_name, fontSize=9, leading=12)

    story: list = []
    story.append(Paragraph(f"{project_title} — 第 {round_number} 轮审查意见", title_style))
    story.append(Spacer(1, 6))

    if gate_passed is not None:
        gate_txt = "通过" if gate_passed else "未通过"
        story.append(Paragraph(f"格式门禁：{gate_txt}（{gate_reason or '—'}）", body_style))
        story.append(Spacer(1, 6))

    if not issues:
        story.append(Paragraph("未发现问题。", body_style))
        doc.build(story)
        return buffer.getvalue()

    headers = ["页码", "级别", "问题", "修改建议"]
    rows = [headers]
    for issue in sorted(issues, key=lambda i: (i.page or 9999, i.severity.value)):
        page = getattr(issue, "page_line", None) or (
            f"第 {issue.page} 页" if issue.page else "—"
        )
        hint = getattr(issue, "revision_hint", None) or issue.suggestion or "—"
        rows.append(
            [
                page,
                issue.severity.value,
                issue.message[:120],
                str(hint)[:80],
            ]
        )

    table = Table(rows, colWidths=[22 * mm, 14 * mm, 75 * mm, 65 * mm], repeatRows=1)
    table.setStyle(
        TableStyle(
            [
                ("FONT", (0, 0), (-1, -1), font_name, 8),
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#f5f5f4")),
                ("GRID", (0, 0), (-1, -1), 0.25, colors.grey),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ]
        )
    )
    story.append(table)
    doc.build(story)
    return buffer.getvalue()
