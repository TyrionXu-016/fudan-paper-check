from __future__ import annotations

import json
from uuid import uuid4

from agents.base import AgentContext
from agents.post_filters import apply_typo_grammar_filters
from schema.models import CheckCategory, DetectStage, Issue, IssueSeverity, IssueType, PaperDocument, Span


class TypoAgent:
    name: str = "TypoAgent"
    stage: DetectStage = DetectStage.TYPO_CHECK

    def run(self, doc: PaperDocument, spans: list[Span], ctx: AgentContext) -> list[Issue]:
        issues: list[Issue] = []
        
        # In a real implementation we would batch spans and send to LLM.
        # Here we mock the behavior.
        for span in spans:
            # Mock retrieving context
            context_snippets = ctx.doc_retriever.retrieve(ctx.task_id, span.id)
            context_text = "\n".join(s.text for s in context_snippets)
            
            messages = [
                {"role": "system", "content": "你是学术论文错别字与语病纠错助手..."},
                {"role": "user", "content": f"【上下文】{context_text}\n【待检】{span.text}"}
            ]
            
            # Using Mock LLM
            # resp = ctx.llm.chat(messages)
            # raw_issues = json.loads(resp)
            raw_issues = []
            
            parsed_issues = []
            for ri in raw_issues:
                parsed_issues.append(
                    Issue(
                        id=str(uuid4()),
                        issue_type=IssueType.TYPO,
                        code="TYPO_LLM",
                        category=CheckCategory.FORMAT,
                        severity=IssueSeverity.WARNING,
                        message=ri.get("message", ""),
                        span_id=span.id,
                        original_text=ri.get("original_text", ""),
                        suggested_text=ri.get("suggested_text", ""),
                        section=span.section_id,
                        line=span.line_start
                    )
                )
                
            filtered = apply_typo_grammar_filters(parsed_issues, span.text)
            issues.extend(filtered)
            
        return issues
