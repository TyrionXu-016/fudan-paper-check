from __future__ import annotations

from agents.base import AgentContext
from checks.format import FormatChecker
from schema.models import DetectStage, Issue, PaperDocument, Span


class FormatAgent:
    name: str = "FormatAgent"
    stage: DetectStage = DetectStage.FORMAT_CHECK

    def run(self, doc: PaperDocument, spans: list[Span], ctx: AgentContext) -> list[Issue]:
        checker = FormatChecker(journal_profile=ctx.rule_base_id)
        issues = checker.check(doc)
        
        # Enrich issues with RAG rule snippets
        for issue in issues:
            if issue.code == "FORMAT_DOI_PATTERN":
                query = "DOI 格式"
            elif issue.code.startswith("FORMAT_CLASSIFICATION"):
                query = "中图分类号"
            elif issue.code == "FORMAT_TABLE_CAPTION":
                query = "表题 题注"
            else:
                query = ""

            if query:
                snippets = ctx.rule_retriever.retrieve(query, dimensions=["format"], top_k=1)
                if snippets:
                    issue.evidence = f"{issue.evidence}\n规范依据: {snippets[0].text}".strip()
                    
        return issues
