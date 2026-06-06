from __future__ import annotations

import json
from uuid import uuid4

from agents.base import AgentContext
from schema.models import CheckCategory, DetectStage, Issue, IssueSeverity, IssueType, PaperDocument, Span


class LogicAgent:
    name: str = "LogicAgent"
    stage: DetectStage = DetectStage.LOGIC_CHECK

    def _build_system_prompt(self) -> str:
        return (
            "你是学术论文逻辑检查助手，主要负责发现上下文矛盾、数值不一致（例如摘要与正文不一致）等逻辑问题。\n"
            "规则：\n"
            "1. 只输出 JSON 对象，格式为 `{\"issues\": [...]}`。如果没有逻辑错误，返回 `{\"issues\": []}`。\n"
            "2. JSON 数组中的每一项必须包含: span_id, original_text, suggested_text (可为空), issue_type (必须为 logic_contradiction), reason, message, evidence (引用冲突的具体上下文)。\n"
            "3. 绝对不得无中生有，仅在存在明确的前后矛盾时才报错。\n"
        )

    def run(self, doc: PaperDocument, spans: list[Span], ctx: AgentContext) -> list[Issue]:
        issues: list[Issue] = []
        
        valid_spans = [s for s in spans if len(s.text) >= 20]
        
        batch_size = 4  # Smaller batch size for logic since it needs more reasoning context
        for i in range(0, len(valid_spans), batch_size):
            batch_spans = valid_spans[i:i+batch_size]
            
            context_text = ""
            for span in batch_spans:
                # We include section summaries for logic checks if doc_retriever supports it
                # For safety, we just fetch standard top_k
                context_snippets = ctx.doc_retriever.retrieve(ctx.task_id, span.id)
                context_text += "\n".join(s.text for s in context_snippets) + "\n"
                
            span_json_list = [{"span_id": s.id, "text": s.text} for s in batch_spans]
            
            messages = [
                {"role": "system", "content": self._build_system_prompt()},
                {"role": "user", "content": f"【全局与局部上下文】\n{context_text[:2000]}\n\n【待检 spans JSON】\n{json.dumps(span_json_list, ensure_ascii=False)}"}
            ]
            
            try:
                resp = ctx.llm.chat(messages, json_mode=True, task_type="logic")
                raw_data = json.loads(resp)
                raw_issues = raw_data.get("issues", [])
                if not isinstance(raw_issues, list):
                    raw_issues = []
            except Exception as e:
                print(f"LogicAgent LLM parsing failed: {e}")
                raw_issues = []
                
            for ri in raw_issues:
                span_id = ri.get("span_id", "")
                target_span = next((s for s in batch_spans if s.id == span_id), None)
                if not target_span:
                    continue
                    
                issues.append(
                    Issue(
                        id=str(uuid4()),
                        issue_type=IssueType.LOGIC_CONTRADICTION,
                        code="LOGIC_LLM",
                        category=CheckCategory.CONSISTENCY,
                        severity=IssueSeverity.WARNING,
                        message=ri.get("message", ri.get("reason", "")),
                        span_id=span_id,
                        original_text=ri.get("original_text", ""),
                        suggested_text=ri.get("suggested_text", ""),
                        evidence=ri.get("evidence", ""),
                        section=target_span.section_id,
                        line=target_span.line_start
                    )
                )
                
            if ctx.publish_progress:
                ctx.publish_progress(self.stage, int((i + batch_size) / len(valid_spans) * 100), f"逻辑检查 {i}/{len(valid_spans)}")
                
        return issues
