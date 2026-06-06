import pytest
from typing import Any
import json
from schema.models import PaperDocument, Span, IssueType
from agents.typo_agent import TypoAgent
from agents.base import AgentContext, DocRetriever

class MockRuleRetriever:
    def retrieve(self, *args, **kwargs):
        return []

class MockDocRetriever(DocRetriever):
    def retrieve(self, task_id, span_id, top_k=5):
        class MockSnippet:
            def __init__(self, text):
                self.text = text
        return [MockSnippet("这是一些上下文。")]

class MockLLMClient:
    def chat(self, messages, *, json_mode=True, timeout=60, task_type=""):
        # Mocking a successful JSON response
        return json.dumps({
            "issues": [
                {
                    "span_id": "s1",
                    "original_text": "算发",
                    "suggested_text": "算法",
                    "issue_type": "typo",
                    "reason": "拼写错误",
                    "message": "应为'算法'"
                }
            ]
        })

def test_typo_agent_run():
    agent = TypoAgent()
    doc = PaperDocument(id="doc1", title="test", sections=[])
    spans = [
        Span(id="s1", section_id="sec1", block_id="b1", text="这种算发非常高效。", start_offset=0, end_offset=10),
        Span(id="s2", section_id="sec1", block_id="b1", text="没有错别字的一句。", start_offset=10, end_offset=20)
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
    assert issue.issue_type == IssueType.TYPO
    assert issue.original_text == "算发"
    assert issue.suggested_text == "算法"
    assert issue.span_id == "s1"
