from __future__ import annotations

import json
from uuid import uuid4

from agents.base import AgentContext
from agents.post_filters import apply_typo_grammar_filters
from schema.models import CheckCategory, DetectStage, Issue, IssueSeverity, IssueType, PaperDocument, Span


class GrammarAgent:
    name: str = "GrammarAgent"
    stage: DetectStage = DetectStage.GRAMMAR_CHECK

    def _build_system_prompt(self) -> str:
        return (
            "你是学术论文语病纠错助手。请检测输入文本中的语法错误、成分残缺、搭配不当和冗余表述。\n"
            "规则：\n"
            "1. 只输出 JSON 对象，格式为 `{\"issues\": [...]}`。如果没有错误，返回 `{\"issues\": []}`。\n"
            "2. JSON 数组中的每一项必须包含: span_id, original_text, suggested_text, issue_type (必须为 grammar), reason, message。\n"
            "3. 绝对不得修改数字、公式、引用标记如 [1]、DOI、单位。\n"
            "4. 仅修改明确的语病，不做润色。修改内容必须能在上下文中自然连贯。\n"
        )

    def run(self, doc: PaperDocument, spans: list[Span], ctx: AgentContext) -> list[Issue]:
        issues: list[Issue] = []
        
        batch_size = 8
        for i in range(0, len(spans), batch_size):
            batch_spans = spans[i:i+batch_size]
            
            context_text = ""
            for span in batch_spans:
                context_snippets = ctx.doc_retriever.retrieve(ctx.task_id, span.id)
                context_text += "\n".join(s.text for s in context_snippets) + "\n"
            
            span_json_list = [{"span_id": s.id, "text": s.text} for s in batch_spans]
            
            messages = [
                {"role": "system", "content": self._build_system_prompt()},
                {"role": "user", "content": f"【上下文片段】\n{context_text[:1500]}\n\n【待检 spans JSON】\n{json.dumps(span_json_list, ensure_ascii=False)}"}
            ]
            
            try:
                resp = ctx.llm.chat(messages, json_mode=True, task_type="grammar")
                raw_data = json.loads(resp)
                raw_issues = raw_data.get("issues", [])
                if not isinstance(raw_issues, list):
                    raw_issues = []
            except Exception as e:
                print(f"GrammarAgent LLM parsing failed: {e}")
                raw_issues = []
            
            parsed_issues = []
            for ri in raw_issues:
                span_id = ri.get("span_id", "")
                target_span = next((s for s in batch_spans if s.id == span_id), None)
                if not target_span:
                    continue
                    
                parsed_issues.append(
                    Issue(
                        id=str(uuid4()),
                        issue_type=IssueType.GRAMMAR,
                        code="GRAMMAR_LLM",
                        category=CheckCategory.FORMAT,
                        severity=IssueSeverity.WARNING,
                        message=ri.get("message", ri.get("reason", "")),
                        span_id=span_id,
                        original_text=ri.get("original_text", ""),
                        suggested_text=ri.get("suggested_text", ""),
                        section=target_span.section_id,
                        line=target_span.line_start
                    )
                )
                
            for span in batch_spans:
                span_issues = [iss for iss in parsed_issues if iss.span_id == span.id]
                filtered = apply_typo_grammar_filters(span_issues, span.text)
                issues.extend(filtered)
            
            if ctx.publish_progress:
                ctx.publish_progress(self.stage, int((i + batch_size) / len(spans) * 100), f"检测段落 {i}/{len(spans)}")
            
        return issues
