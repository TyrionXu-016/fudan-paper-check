from __future__ import annotations

import re

from checks.base import BaseChecker, load_journal_profile
from schema.models import CheckCategory, Issue, IssueSeverity, PaperDocument


def _normalize_identifier_spacing(text: str) -> str:
    text = re.sub(r"(?<=[A-Za-z0-9])\.\s+(?=[A-Za-z0-9])", ".", text)
    text = re.sub(r"(?<=[A-Za-z0-9])/\s+(?=[A-Za-z0-9])", "/", text)
    text = re.sub(r"(?<=[A-Za-z0-9])-\s+(?=[A-Za-z0-9])", "-", text)
    return text


class FormatChecker(BaseChecker):
    category = CheckCategory.FORMAT

    def __init__(self, journal_profile: str = "generic") -> None:
        self.profile = load_journal_profile(journal_profile)
        self.patterns = self.profile.get("patterns", {})
        self.warnings = self.profile.get("warnings", {})

    def check(self, doc: PaperDocument) -> list[Issue]:
        issues: list[Issue] = []
        full_text = "\n".join(b.raw for b in doc.blocks)

        if self.patterns.get("doi") and doc.meta.doi:
            normalized_full_text = _normalize_identifier_spacing(full_text)
            if not re.search(self.patterns["doi"], normalized_full_text, re.I):
                issues.append(
                    Issue(
                        code="FORMAT_DOI_PATTERN",
                        category=self.category,
                        severity=IssueSeverity.WARNING,
                        message="DOI 格式与期刊模板不完全匹配",
                        evidence=doc.meta.doi,
                    )
                )
        elif self.patterns.get("doi"):
            issues.append(
                Issue(
                    code="FORMAT_MISSING_DOI",
                    category=self.category,
                    severity=IssueSeverity.INFO,
                    message="未检测到 DOI",
                )
            )

        if self.patterns.get("classification"):
            if doc.meta.classification:
                if not re.search(
                    self.patterns["classification"], full_text
                ):
                    issues.append(
                        Issue(
                            code="FORMAT_CLASSIFICATION",
                            category=self.category,
                            severity=IssueSeverity.INFO,
                            message="中图分类号存在但格式需人工核对",
                            evidence=doc.meta.classification,
                        )
                    )
            else:
                issues.append(
                    Issue(
                        code="FORMAT_MISSING_CLASSIFICATION",
                        category=self.category,
                        severity=IssueSeverity.WARNING,
                        message="未检测到中图分类号",
                    )
                )

        ocr_pat = self.warnings.get("ocr_space_in_number")
        if ocr_pat:
            evidences: list[str] = []
            seen: set[str] = set()
            first_line: int | None = None
            for block in doc.blocks:
                raw = block.raw or block.text
                if "doi:" in raw.lower():
                    continue
                for m in re.finditer(ocr_pat, raw):
                    evidence = m.group(0)
                    if evidence in seen:
                        continue
                    seen.add(evidence)
                    evidences.append(evidence)
                    if first_line is None:
                        first_line = block.line_start
            if evidences:
                issues.append(
                    Issue(
                        code="FORMAT_OCR_NUMBER_SPACE",
                        category=self.category,
                        severity=IssueSeverity.WARNING,
                        line=first_line,
                        message=f"检测到 {len(evidences)} 处数值中可能存在 OCR 多余空格",
                        suggestion="检查并合并数字中的空格，如 42. 29 → 42.29",
                        evidence="; ".join(evidences[:12]),
                    )
                )

        formula_nums = [int(x) for x in re.findall(r"\\tag\s*\{(\d+)\}", full_text)]
        formula_nums += [int(x) for x in re.findall(r"\((\d+)\)\s*$", full_text) if int(x) < 30]
        if formula_nums:
            expected = list(range(1, max(formula_nums) + 1))
            missing = [n for n in expected if n not in formula_nums]
            if missing and len(missing) <= 3:
                issues.append(
                    Issue(
                        code="FORMAT_FORMULA_NUMBER_GAP",
                        category=self.category,
                        severity=IssueSeverity.INFO,
                        message=f"公式编号可能不连续，缺失: {missing}",
                    )
                )

        for table in doc.tables:
            if table.number and not table.caption:
                issues.append(
                    Issue(
                        code="FORMAT_TABLE_CAPTION",
                        category=self.category,
                        severity=IssueSeverity.WARNING,
                        message=f"表 {table.number} 缺少题注",
                    )
                )

        return issues
