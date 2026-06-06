from __future__ import annotations

from agents.base import AgentContext
from checks.structure import StructureChecker
from schema.models import DetectStage, Issue, PaperDocument, Span


class StructureAgent:
    name: str = "StructureAgent"
    stage: DetectStage = DetectStage.FORMAT_CHECK  # Usually grouped with format

    def run(self, doc: PaperDocument, spans: list[Span], ctx: AgentContext) -> list[Issue]:
        checker = StructureChecker(journal_profile=ctx.rule_base_id)
        issues = checker.check(doc)
        
        for issue in issues:
            query = ""
            if issue.code == "STRUCT_MISSING_SECTION":
                query = f"章节结构 缺少 {issue.section}"
            elif issue.code == "STRUCT_MISSING_ABSTRACT":
                query = "摘要 摘要段落"
            elif issue.code == "STRUCT_EMPTY_REFERENCES":
                query = "参考文献 列表"
            
            if query:
                snippets = ctx.rule_retriever.retrieve(query, dimensions=["format"], top_k=1)
                if snippets:
                    evidence = issue.evidence or ""
                    issue.evidence = f"{evidence}\n规范依据: {snippets[0].text}".strip()
                    
        return issues
