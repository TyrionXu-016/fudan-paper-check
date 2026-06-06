from __future__ import annotations

import json
import os
from uuid import uuid4

from agents.base import AgentContext
from schema.models import CheckCategory, DetectStage, Issue, IssueSeverity, IssueType, PaperDocument, Span


class PolishAgent:
    name: str = "PolishAgent"
    stage: DetectStage = DetectStage.POLISH

    def _build_system_prompt(self) -> str:
        return (
            "你是学术论文润色助手。请对输入文本中的表述口语化、长句难懂等问题提供改进建议。\n"
            "规则：\n"
            "1. 只输出 JSON 对象，格式为 `{\"issues\": [...]}`。如果无需润色，返回 `{\"issues\": []}`。\n"
            "2. JSON 数组中的每一项必须包含: span_id, original_text, suggested_text, issue_type (必须是 polish, paragraph_logic, 或 sentence_split 之一), message。\n"
            "3. 绝对不改变原意、不篡改数据、公式和专用名词。\n"
            "4. 仅提供改进建议，severity 为 INFO级别。\n"
        )

    def run(self, doc: PaperDocument, spans: list[Span], ctx: AgentContext) -> list[Issue]:
        issues: list[Issue] = []
        
        # Determine if enabled from ctx.config or os env
        polish_enabled = ctx.config.get("POLISH_ENABLED", os.getenv("POLISH_ENABLED", "true")).lower() == "true"
        if not polish_enabled:
            return issues
            
        # Filter out very short spans
        valid_spans = [s for s in spans if len(s.text) >= 15]
        
        batch_size = 8
        for i in range(0, len(valid_spans), batch_size):
            batch_spans = valid_spans[i:i+batch_size]
            
            context_text = ""
            for span in batch_spans:
                context_snippets = ctx.doc_retriever.retrieve(ctx.task_id, span.id)
                context_text += "\n".join(s.text for s in context_snippets) + "\n"
                
            span_json_list = [{"span_id": s.id, "text": s.text} for s in batch_spans]
            
            messages = [
                {"role": "system", "content": self._build_system_prompt()},
                {"role": "user", "content": f"【上下文片段】\n{context_text[:1500]}\n\n【待润色 spans JSON】\n{json.dumps(span_json_list, ensure_ascii=False)}"}
            ]
            
            try:
                resp = ctx.llm.chat(messages, json_mode=True, task_type="polish")
                raw_data = json.loads(resp)
                raw_issues = raw_data.get("issues", [])
                if not isinstance(raw_issues, list):
                    raw_issues = []
            except Exception as e:
                print(f"PolishAgent LLM parsing failed: {e}")
                raw_issues = []
                
            for ri in raw_issues:
                span_id = ri.get("span_id", "")
                target_span = next((s for s in batch_spans if s.id == span_id), None)
                if not target_span:
                    continue
                    
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
                        message=ri.get("message", ri.get("reason", "")),
                        span_id=span_id,
                        original_text=ri.get("original_text", ""),
                        suggested_text=ri.get("suggested_text", ""),
                        section=target_span.section_id,
                        line=target_span.line_start
                    )
                )
                
            if ctx.publish_progress:
                ctx.publish_progress(self.stage, int((i + batch_size) / len(valid_spans) * 100), f"润色段落 {i}/{len(valid_spans)}")
                
        return issues
