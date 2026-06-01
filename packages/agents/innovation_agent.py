from __future__ import annotations

import os

from agents.llm_client import LLMClient, llm_client
from agents.prompts import load_prompt
from checks.base import section_text
from schema.models import PaperDocument


class InnovationAgent:
    def __init__(self, client: LLMClient | None = None) -> None:
        self.client = client or llm_client

    def analyze(self, doc: PaperDocument) -> dict:
        ctx = self._build_context(doc)
        if not self.client.is_available():
            return self._fallback(ctx)
        system = load_prompt("innovation.system.md")
        user = self._render_user(ctx)
        try:
            model = os.getenv("LLM_MODEL_REASONING") or os.getenv("LLM_MODEL", "deepseek-chat")
            return self.client.complete_json(system, user, model=model)
        except Exception:
            return self._fallback(ctx)

    def _build_context(self, doc: PaperDocument) -> dict:
        title = doc.meta.title or "（未识别标题）"
        abstract = doc.meta.abstract or section_text(doc, "abstract")
        method = section_text(doc, "method") or section_text(doc, "experiment")
        conclusion = section_text(doc, "conclusion")
        refs = doc.references or []
        top_titles = [r.title for r in refs[:10] if getattr(r, "title", None)]
        return {
            "title": title,
            "abstract": abstract,
            "method_excerpt": method,
            "conclusion_excerpt": conclusion,
            "ref_count": len(refs),
            "top_ref_titles": top_titles,
        }

    def _render_user(self, ctx: dict) -> str:
        lines = [
            f"【论文标题】{ctx['title']}",
            f"【中文摘要】{ctx['abstract'][:2000]}",
            f"【方法章节摘录】{ctx['method_excerpt'][:4000]}",
            f"【结论章节摘录】{ctx['conclusion_excerpt'][:2000]}",
            f"【参考文献数量】{ctx['ref_count']}",
            "【代表文献标题（前10条）】",
        ]
        for t in ctx["top_ref_titles"]:
            lines.append(f"- {t[:150]}")
        return "\n".join(lines)

    def _fallback(self, ctx: dict) -> dict:
        abstract = ctx["abstract"][:300] or "（摘要缺失）"
        ref_n = ctx["ref_count"]
        method_len = len(ctx["method_excerpt"])
        score = 0.45
        if method_len > 2000:
            score += 0.1
        if ref_n >= 20:
            score += 0.05
        score = min(0.75, score)
        return {
            "llm_summary": (
                f"基于摘要与方法章节的规则预审：论文《{ctx['title']}》"
                f"摘要约 {len(ctx['abstract'])} 字，方法章节约 {method_len} 字，"
                f"参考文献 {ref_n} 篇。建议在导师终审时重点核对创新点表述与实验支撑。"
                f"摘要摘录：{abstract[:120]}…"
            ),
            "novelty_score": round(score, 2),
            "comparison_notes": (
                "未启用 LLM，无法与领域文献自动对比。"
                "请导师结合代表文献与方法章节人工评估创新性。"
            ),
            "strengths": ["方法章节有一定篇幅" if method_len > 500 else "结构完整"],
            "weaknesses": ["LLM 预审未运行，创新点需人工确认"],
            "suggested_questions_for_advisor": [
                "与现有方法相比，核心创新点是什么？",
                "实验是否充分支撑结论中的 claim？",
            ],
        }
