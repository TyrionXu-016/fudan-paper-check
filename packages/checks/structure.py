from __future__ import annotations

import re

from checks.base import BaseChecker, load_journal_profile, section_text
from schema.models import CheckCategory, Issue, IssueSeverity, PaperDocument, SectionKind


class StructureChecker(BaseChecker):
    category = CheckCategory.STRUCTURE

    def __init__(self, journal_profile: str = "generic") -> None:
        self.profile = load_journal_profile(journal_profile)

    def check(self, doc: PaperDocument) -> list[Issue]:
        issues: list[Issue] = []
        kinds = {s.kind for s in doc.sections}

        def has_required_section(kind: SectionKind) -> bool:
            if kind in kinds:
                return True
            if kind == SectionKind.ABSTRACT:
                return bool(doc.meta.abstract)
            if kind == SectionKind.KEYWORDS:
                return bool(doc.meta.keywords)
            if kind == SectionKind.REFERENCES:
                return bool(doc.references)
            return False

        for req in self.profile.get("required_sections", []):
            try:
                sk = SectionKind(req)
            except ValueError:
                continue
            if not has_required_section(sk):
                issues.append(
                    Issue(
                        code="STRUCT_MISSING_SECTION",
                        category=self.category,
                        severity=IssueSeverity.ERROR,
                        section=req,
                        message=f"缺少必需章节：{req}",
                        suggestion="补充对应章节或检查解析结果",
                    )
                )

        if not (doc.meta.abstract or section_text(doc, "abstract").strip()):
            issues.append(
                Issue(
                    code="STRUCT_MISSING_ABSTRACT",
                    category=self.category,
                    severity=IssueSeverity.ERROR,
                    message="未检测到摘要内容",
                    suggestion="确认摘要段落存在且格式为「摘 要:」",
                )
            )

        if not (doc.references or section_text(doc, "references").strip()):
            issues.append(
                Issue(
                    code="STRUCT_EMPTY_REFERENCES",
                    category=self.category,
                    severity=IssueSeverity.ERROR,
                    section="references",
                    message="参考文献列表为空",
                    suggestion="补充参考文献章节",
                )
            )

        numbered = [
            s for s in doc.sections if re.match(r"^\d+", s.title.strip())
        ]
        for i in range(1, len(numbered)):
            prev_num = re.match(r"^(\d+(?:\.\d+)*)", numbered[i - 1].title)
            curr_num = re.match(r"^(\d+(?:\.\d+)*)", numbered[i].title)
            if prev_num and curr_num:
                prev_parts = [int(x) for x in prev_num.group(1).split(".")]
                curr_parts = [int(x) for x in curr_num.group(1).split(".")]
                if curr_parts[0] < prev_parts[0]:
                    issues.append(
                        Issue(
                            code="STRUCT_SECTION_ORDER",
                            category=self.category,
                            severity=IssueSeverity.WARNING,
                            section=numbered[i].title,
                            line=numbered[i].start_line,
                            message=f"章节编号可能不连续：{numbered[i-1].title} → {numbered[i].title}",
                            evidence=numbered[i].title,
                        )
                    )

        fig_nums = {f.number for f in doc.figures if f.number}
        body = "\n".join(b.text for b in doc.blocks)
        for ref in re.findall(r"图\s*(\d+)", body):
            n = int(ref)
            if n not in fig_nums:
                issues.append(
                    Issue(
                        code="STRUCT_FIGURE_REF_MISSING",
                        category=self.category,
                        severity=IssueSeverity.WARNING,
                        message=f"正文引用图 {n}，但未找到对应图题",
                        suggestion="检查图题或图片解析结果",
                        evidence=f"图 {n}",
                    )
                )

        table_nums = {t.number for t in doc.tables if t.number}
        for ref in re.findall(r"表\s*(\d+)", body):
            n = int(ref)
            if n not in table_nums:
                issues.append(
                    Issue(
                        code="STRUCT_TABLE_REF_MISSING",
                        category=self.category,
                        severity=IssueSeverity.WARNING,
                        message=f"正文引用表 {n}，但未找到对应表格",
                        evidence=f"表 {n}",
                    )
                )

        return issues
