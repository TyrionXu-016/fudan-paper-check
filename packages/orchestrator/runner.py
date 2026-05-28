from __future__ import annotations

from schema.models import (
    CheckCategory,
    CheckReport,
    DetectStage,
    Issue,
    IssueSeverity,
    PaperDocument,
    ReportSummary,
)
from checks.consistency import ConsistencyChecker
from checks.format import FormatChecker
from checks.reference import ReferenceChecker
from checks.structure import StructureChecker


CHECK_STAGE_PROGRESS: dict[CheckCategory, tuple[DetectStage, int, str]] = {
    CheckCategory.STRUCTURE: (DetectStage.FORMAT_CHECK, 35, "正在检查章节结构"),
    CheckCategory.FORMAT: (DetectStage.FORMAT_CHECK, 50, "正在检查格式规范"),
    CheckCategory.REFERENCE: (DetectStage.REFERENCE_CHECK, 75, "正在检查参考文献"),
    CheckCategory.CONSISTENCY: (DetectStage.LOGIC_CHECK, 90, "正在检查内容与一致性"),
}


class CheckOrchestrator:
    def __init__(self, journal_profile: str = "generic", llm_enabled: bool | None = None) -> None:
        self.journal_profile = journal_profile
        self.checkers = [
            StructureChecker(journal_profile),
            FormatChecker(journal_profile),
            ReferenceChecker(),
            ConsistencyChecker(llm_enabled=llm_enabled),
        ]

    def run(
        self,
        doc: PaperDocument,
        job_id: str,
        on_progress=None,
    ) -> CheckReport:
        all_issues: list[Issue] = []
        checks_run: list[CheckCategory] = []

        for checker in self.checkers:
            if on_progress is not None:
                stage, percent, message = CHECK_STAGE_PROGRESS[checker.category]
                on_progress(stage, percent, message)
            if doc.quality.degraded and checker.category in {
                CheckCategory.CONSISTENCY,
                CheckCategory.REFERENCE,
            }:
                issues = checker.check(doc)
                for issue in issues:
                    if issue.severity == IssueSeverity.ERROR:
                        issue.severity = IssueSeverity.WARNING
                        issue.message = f"[解析质量降级] {issue.message}"
                all_issues.extend(issues)
            else:
                all_issues.extend(checker.check(doc))
            checks_run.append(checker.category)

        merged = self._merge_issues(all_issues)
        summary = ReportSummary(
            errors=sum(1 for i in merged if i.severity == IssueSeverity.ERROR),
            warnings=sum(1 for i in merged if i.severity == IssueSeverity.WARNING),
            infos=sum(1 for i in merged if i.severity == IssueSeverity.INFO),
        )
        return CheckReport(
            job_id=job_id,
            parse_quality=doc.quality,
            summary=summary,
            issues=sorted(
                merged,
                key=lambda i: (
                    0 if i.severity == IssueSeverity.ERROR else 1
                    if i.severity == IssueSeverity.WARNING
                    else 2,
                    i.line or 0,
                ),
            ),
            checks_run=checks_run,
            paper_title=doc.meta.title,
        )

    def _merge_issues(self, issues: list[Issue]) -> list[Issue]:
        seen: dict[tuple[str, str | None, int | None], Issue] = {}
        for issue in issues:
            key = (issue.code, issue.section, issue.line)
            if key not in seen:
                seen[key] = issue
            else:
                existing = seen[key]
                if issue.evidence and issue.evidence not in existing.evidence:
                    existing.evidence = f"{existing.evidence}; {issue.evidence}".strip("; ")
        return list(seen.values())


def report_to_markdown(report: CheckReport) -> str:
    lines = [
        f"# 论文预检查报告",
        "",
        f"**论文标题：** {report.paper_title or '（未识别）'}",
        f"**任务 ID：** {report.job_id}",
        "",
        "## 解析质量",
        f"- 融合得分：{report.parse_quality.fusion_score}",
        f"- Maker 得分：{report.parse_quality.maker_score}",
        f"- MinerU 得分：{report.parse_quality.mineru_score}",
    ]
    for w in report.parse_quality.fusion_warnings:
        lines.append(f"- ⚠ {w}")
    lines.extend(
        [
            "",
            "## 摘要",
            f"- 错误：{report.summary.errors}",
            f"- 警告：{report.summary.warnings}",
            f"- 提示：{report.summary.infos}",
            "",
            "## 问题列表",
            "",
        ]
    )
    if not report.issues:
        lines.append("未发现问题。")
    else:
        for issue in report.issues:
            loc = []
            if issue.section:
                loc.append(issue.section)
            if issue.line:
                loc.append(f"L{issue.line}")
            loc_str = f" ({', '.join(loc)})" if loc else ""
            lines.append(
                f"- **[{issue.severity.value}]** `{issue.code}`{loc_str}: {issue.message}"
            )
            if issue.suggestion:
                lines.append(f"  - 建议：{issue.suggestion}")
            if issue.evidence:
                lines.append(f"  - 证据：{issue.evidence[:200]}")
    return "\n".join(lines)
