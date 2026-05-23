from __future__ import annotations

import re

from checks.base import BaseChecker
from schema.models import CheckCategory, Issue, IssueSeverity, PaperDocument


class ReferenceChecker(BaseChecker):
    category = CheckCategory.REFERENCE

    def check(self, doc: PaperDocument) -> list[Issue]:
        issues: list[Issue] = []
        if doc.quality.degraded:
            downgrade = True
        else:
            downgrade = False

        ref_indices = {r.index for r in doc.references}
        cited_indices: set[int] = set()
        for c in doc.citations:
            cited_indices.update(c.ref_indices)

        if not ref_indices:
            return issues

        for idx in sorted(cited_indices):
            if idx not in ref_indices:
                issues.append(
                    Issue(
                        code="REF_CITATION_ORPHAN",
                        category=self.category,
                        severity=IssueSeverity.WARNING if downgrade else IssueSeverity.ERROR,
                        message=f"正文引用 [{idx}]，但参考文献列表中不存在",
                        suggestion="补充参考文献条目或修正引用编号",
                        evidence=f"[{idx}]",
                    )
                )

        max_cited = max(cited_indices) if cited_indices else 0
        for idx in range(1, max_cited + 1):
            if idx not in cited_indices and idx in ref_indices:
                issues.append(
                    Issue(
                        code="REF_UNCITED",
                        category=self.category,
                        severity=IssueSeverity.INFO,
                        message=f"参考文献 [{idx}] 在正文中未被引用",
                        evidence=doc.references[idx - 1].raw_text[:80]
                        if idx <= len(doc.references)
                        else "",
                    )
                )

        sorted_refs = sorted(ref_indices)
        for i in range(1, len(sorted_refs)):
            if sorted_refs[i] - sorted_refs[i - 1] > 1:
                gap = list(range(sorted_refs[i - 1] + 1, sorted_refs[i]))
                issues.append(
                    Issue(
                        code="REF_INDEX_GAP",
                        category=self.category,
                        severity=IssueSeverity.WARNING,
                        message=f"参考文献编号跳号：缺失 {gap}",
                    )
                )
                break

        seen: dict[str, int] = {}
        for ref in doc.references:
            key = re.sub(r"\s+", "", ref.raw_text[:60])
            if key in seen:
                issues.append(
                    Issue(
                        code="REF_DUPLICATE",
                        category=self.category,
                        severity=IssueSeverity.WARNING,
                        message=f"参考文献 [{ref.index}] 与 [{seen[key]}] 可能重复",
                        evidence=ref.raw_text[:100],
                    )
                )
            seen[key] = ref.index

            if not self._has_basic_fields(ref.raw_text):
                issues.append(
                    Issue(
                        code="REF_INCOMPLETE_ENTRY",
                        category=self.category,
                        severity=IssueSeverity.WARNING,
                        message=f"参考文献 [{ref.index}] 字段可能不完整",
                        evidence=ref.raw_text[:120],
                        suggestion="核对作者、题名、期刊、年卷期页",
                    )
                )

        return issues

    @staticmethod
    def _has_basic_fields(text: str) -> bool:
        has_author = bool(re.search(r"[\u4e00-\u9fffA-Za-z]", text))
        has_year = bool(re.search(r"\b(19|20)\d{2}\b", text))
        has_journal_marker = any(m in text for m in ["[J]", "[M]", "[C]", "[D]"])
        return has_author and (has_year or has_journal_marker)
