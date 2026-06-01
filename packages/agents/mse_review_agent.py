from __future__ import annotations

import uuid

from agents.llm_client import LLMClient, llm_client
from agents.post_filters import apply_mse_post_filters
from agents.prompts import load_prompt, render_mse_review_user
from mse.chunker import SectionChunk, iter_section_chunks
from rag.mse_rule_retriever import retrieve_project_rules
from schema.models import CheckCategory, Issue, IssueSeverity, IssueType


_CATEGORY_MAP = {
    "structure": CheckCategory.STRUCTURE,
    "format": CheckCategory.FORMAT,
    "reference": CheckCategory.REFERENCE,
    "consistency": CheckCategory.CONSISTENCY,
}

_SEVERITY_MAP = {
    "error": IssueSeverity.ERROR,
    "warning": IssueSeverity.WARNING,
    "info": IssueSeverity.INFO,
}


class MseReviewAgent:
    def __init__(self, client: LLMClient | None = None) -> None:
        self.client = client or llm_client

    def review_chunk(
        self,
        chunk: SectionChunk,
        *,
        project_id: str,
        journal_profile: str = "generic",
    ) -> list[Issue]:
        query = f"{chunk.title} {chunk.text[:500]}"
        retrieved = retrieve_project_rules(
            project_id, query, top_k=5, journal_profile=journal_profile
        )
        snippets = [r.text for r in retrieved.results]
        rule_refs = {r.text[:80]: r.id for r in retrieved.results}

        if not self.client.is_available():
            return self._fallback_review(chunk, snippets)

        system = load_prompt("mse_review_system.md")
        user = render_mse_review_user(
            section_title=chunk.title,
            section_text=chunk.text,
            rule_snippets=snippets,
            page_start=chunk.page_start,
            page_end=chunk.page_end,
        )
        try:
            data = self.client.complete_json(system, user)
        except Exception as exc:
            return [
                Issue(
                    code="MSE_LLM_SKIP",
                    category=CheckCategory.CONSISTENCY,
                    severity=IssueSeverity.INFO,
                    message=f"章节「{chunk.title}」LLM 审阅跳过：{exc}",
                    section=chunk.title,
                    issue_type=IssueType.LLM,
                )
            ]
        return self._parse_response(data, chunk, rule_refs)

    def _parse_response(
        self,
        data: dict,
        chunk: SectionChunk,
        rule_refs: dict[str, str],
    ) -> list[Issue]:
        issues: list[Issue] = []
        for raw in data.get("issues") or []:
            cat = _CATEGORY_MAP.get(str(raw.get("category", "format")).lower(), CheckCategory.FORMAT)
            sev = _SEVERITY_MAP.get(str(raw.get("severity", "warning")).lower(), IssueSeverity.WARNING)
            rule_ref = raw.get("rule_ref")
            if not rule_ref:
                for key, rid in rule_refs.items():
                    if key in str(raw.get("message", "")):
                        rule_ref = rid
                        break
            issues.append(
                Issue(
                    id=str(uuid.uuid4()),
                    code=str(raw.get("code") or "MSE_LLM"),
                    category=cat,
                    severity=sev,
                    message=str(raw.get("message") or "需修改"),
                    original_text=str(raw.get("original_text") or "")[:500],
                    suggested_text=str(raw.get("suggested_text") or "")[:500],
                    revision_hint=str(raw.get("revision_hint") or raw.get("suggested_text") or "")[:200],
                    rule_ref=rule_ref,
                    page=raw.get("page") or chunk.page_start,
                    line=raw.get("line"),
                    section=chunk.title,
                    issue_type=IssueType.LLM,
                )
            )
        return apply_mse_post_filters(issues)

    def _fallback_review(self, chunk: SectionChunk, snippets: list[str]) -> list[Issue]:
        """Heuristic checks when LLM is unavailable."""
        issues: list[Issue] = []
        text = chunk.text
        if len(text) > 8000:
            issues.append(
                Issue(
                    code="MSE_SECTION_LONG",
                    category=CheckCategory.FORMAT,
                    severity=IssueSeverity.INFO,
                    message=f"章节「{chunk.title}」较长，建议拆分段落便于审阅",
                    section=chunk.title,
                    page=chunk.page_start,
                    issue_type=IssueType.FORMAT,
                )
            )
        if "TODO" in text or "待补充" in text:
            issues.append(
                Issue(
                    code="MSE_PLACEHOLDER",
                    category=CheckCategory.FORMAT,
                    severity=IssueSeverity.WARNING,
                    message=f"章节「{chunk.title}」含占位或未完稿表述",
                    section=chunk.title,
                    page=chunk.page_start,
                    issue_type=IssueType.FORMAT,
                )
            )
        if snippets and "图表" in snippets[0] and "图" not in text and "表" not in text:
            pass
        return issues
