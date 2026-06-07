from __future__ import annotations

from agents.base import AgentContext
from checks.reference import ReferenceChecker
from schema.models import DetectStage, Issue, PaperDocument, Span


class ReferenceAgent:
    name: str = "ReferenceAgent"
    stage: DetectStage = DetectStage.REFERENCE_CHECK

    def run(self, doc: PaperDocument, spans: list[Span], ctx: AgentContext) -> list[Issue]:
        checker = ReferenceChecker()
        issues = checker.check(doc)
        
        for issue in issues:
            query = ""
            if issue.code == "REF_CITATION_ORPHAN" or issue.code == "REF_UNCITED":
                query = "参考文献 引用标记 正文"
            elif issue.code == "REF_INDEX_GAP":
                query = "参考文献 编号 顺序"
            elif issue.code == "REF_INCOMPLETE_ENTRY":
                query = "参考文献 著录格式 字段"
            
            if query:
                snippets = ctx.rule_retriever.retrieve(query, dimensions=["reference"], top_k=1)
                if snippets:
                    evidence = issue.evidence or ""
                    issue.evidence = f"{evidence}\n规范依据: {snippets[0].text}".strip()
                    
        return issues
