from __future__ import annotations

import json
import os
from uuid import uuid4

from agents.base import AgentContext
from schema.models import CheckCategory, DetectStage, Issue, IssueSeverity, IssueType, PaperDocument, Span


class PolishAgent:
    name: str = "PolishAgent"
    stage: DetectStage = DetectStage.POLISH

    def run(self, doc: PaperDocument, spans: list[Span], ctx: AgentContext) -> list[Issue]:
        issues: list[Issue] = []
        
        polish_enabled = os.getenv("POLISH_ENABLED", "true").lower() == "true"
        if not polish_enabled:
            return issues
            
        for span in spans:
            if len(span.text) < 15:
                continue
                
            context_snippets = ctx.doc_retriever.retrieve(ctx.task_id, span.id)
            context_text = "\n".join(s.text for s in context_snippets)
            
            messages = [
                {"role": "system", "content": "你是学术润色助手。仅对表述口语化、长句难懂的句子进行建议。不改变观点和数据。"},
                {"role": "user", "content": f"【上下文】{context_text}\n【待润色】{span.text}"}
            ]
            
            # resp = ctx.llm.chat(messages)
            # raw_issues = json.loads(resp)
            raw_issues = []
            
            for ri in raw_issues:
                i_type_str = ri.get("issue_type", "polish").lower()
                if i_type_str == "paragraph_logic":
                    i_type = IssueType.PARAGRAPH_LOGIC
                elif i_type_str == "sentence_split":
                    i_type = IssueType.SENTENCE_SPLIT
                else:
                    i_type = IssueType.POLISH

                issues.append(
                    Issue(
                        id=str(uuid4()),
                        issue_type=i_type,
                        code="POLISH_LLM",
                        category=CheckCategory.FORMAT,
                        severity=IssueSeverity.INFO, # Always INFO for polish
                        message=ri.get("message", ""),
                        span_id=span.id,
                        original_text=ri.get("original_text", ""),
                        suggested_text=ri.get("suggested_text", ""),
                        section=span.section_id,
                        line=span.line_start
                    )
                )
                
        return issues
