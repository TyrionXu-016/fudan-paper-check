from __future__ import annotations

import json
from uuid import uuid4

from agents.base import AgentContext
from schema.models import CheckCategory, DetectStage, Issue, IssueSeverity, IssueType, PaperDocument, Span


class LogicAgent:
    name: str = "LogicAgent"
    stage: DetectStage = DetectStage.LOGIC_CHECK

    def run(self, doc: PaperDocument, spans: list[Span], ctx: AgentContext) -> list[Issue]:
        issues: list[Issue] = []
        
        for span in spans:
            # We skip short spans or non-paragraph blocks for logic check
            if len(span.text) < 20:
                continue
                
            context_snippets = ctx.doc_retriever.retrieve(ctx.task_id, span.id, include_section_summary=True)
            context_text = "\n".join(s.text for s in context_snippets)
            
            messages = [
                {"role": "system", "content": "你是论文逻辑检查助手，主要负责摘要与正文的数值一致性、语义矛盾等检查..."},
                {"role": "user", "content": f"【上下文】{context_text}\n【待检】{span.text}"}
            ]
            
            # resp = ctx.llm.chat(messages)
            # raw_issues = json.loads(resp)
            raw_issues = []
            
            for ri in raw_issues:
                issues.append(
                    Issue(
                        id=str(uuid4()),
                        issue_type=IssueType.LOGIC_CONTRADICTION,
                        code="LOGIC_LLM",
                        category=CheckCategory.CONSISTENCY,
                        severity=IssueSeverity.WARNING,
                        message=ri.get("message", ""),
                        span_id=span.id,
                        original_text=ri.get("original_text", ""),
                        suggested_text=ri.get("suggested_text", ""),
                        evidence=ri.get("evidence", ""),
                        section=span.section_id,
                        line=span.line_start
                    )
                )
                
        return issues
