import pytest
from typing import Any
import json
from schema.models import PaperDocument, Span, IssueType, IssueSeverity
from agents.logic_agent import LogicAgent
from agents.base import AgentContext, DocRetriever

class MockRuleRetriever:
    def retrieve(self, *args, **kwargs):
        return []

class MockDocRetriever(DocRetriever):
    def retrieve(self, task_id, span_id, top_k=5, include_section_summary=False):
        class MockSnippet:
            def __init__(self, text):
                self.text = text
        return [MockSnippet("摘要指出实验样本量为500。")]

class MockLLMClient:
    def chat(self, messages, *, json_mode=True, timeout=60, task_type=""):
        return json.dumps({
            "issues": [
                {
                    "span_id": "s1",
                    "original_text": "在我们的实验中，共有400名志愿者参与。",
                    "suggested_text": "",
                    "issue_type": "logic_contradiction",
                    "reason": "数值矛盾",
                    "message": "正文提到400名志愿者，与摘要中500样本量矛盾。",
                    "evidence": "摘要指出实验样本量为500。"
                }
            ]
        })

def test_logic_agent_run():
    agent = LogicAgent()
    doc = PaperDocument(id="doc1", title="test", sections=[])
    spans = [
        # Must be >= 20 chars
        Span(id="s1", section_id="sec1", block_id="b1", text="在我们的实验中，共有400名志愿者参与。", start_offset=0, end_offset=21),
    ]
    ctx = AgentContext(
        task_id="task1",
        rule_base_id="r1",
        rule_retriever=MockRuleRetriever(),
        doc_retriever=MockDocRetriever("task1"),
        llm=MockLLMClient(),
        publish_progress=lambda stage, pct, msg: None,
        config={}
    )
    
    issues = agent.run(doc, spans, ctx)
    assert len(issues) == 1
    issue = issues[0]
    assert issue.issue_type == IssueType.LOGIC_CONTRADICTION
    assert issue.span_id == "s1"
    assert issue.evidence == "摘要指出实验样本量为500。"
