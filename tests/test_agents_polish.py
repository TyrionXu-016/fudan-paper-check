import pytest
from typing import Any
import json
from schema.models import PaperDocument, Span, IssueType, IssueSeverity
from agents.polish_agent import PolishAgent
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
                    "original_text": "这个东西确实是非常的好用的，大家都喜欢。",
                    "suggested_text": "该设备具有显著的易用性，广受好评。",
                    "issue_type": "polish",
                    "reason": "口语化严重",
                    "message": "建议改为学术表述"
                }
            ]
        })

def test_polish_agent_run():
    agent = PolishAgent()
    doc = PaperDocument(id="doc1", title="test", sections=[])
    spans = [
        # length must be >= 15 for PolishAgent
        Span(id="s1", section_id="sec1", block_id="b1", text="这个东西确实是非常的好用的，大家都喜欢。", start_offset=0, end_offset=21),
        Span(id="s2", section_id="sec1", block_id="b1", text="这段文字很短", start_offset=21, end_offset=27) # length < 15, should be skipped
    ]
    ctx = AgentContext(
        task_id="task1",
        rule_base_id="r1",
        rule_retriever=MockRuleRetriever(),
        doc_retriever=MockDocRetriever("task1"),
        llm=MockLLMClient(),
        publish_progress=lambda stage, pct, msg: None,
        config={"POLISH_ENABLED": "true"}
    )
    
    issues = agent.run(doc, spans, ctx)
    assert len(issues) == 1
    issue = issues[0]
    assert issue.issue_type == IssueType.POLISH
    assert issue.original_text == "这个东西确实是非常的好用的，大家都喜欢。"
    assert issue.suggested_text == "该设备具有显著的易用性，广受好评。"
    assert issue.span_id == "s1"
    assert issue.severity == IssueSeverity.INFO

def test_polish_agent_disabled():
    agent = PolishAgent()
    doc = PaperDocument(id="doc1", title="test", sections=[])
    spans = [
        Span(id="s1", section_id="sec1", block_id="b1", text="这个东西确实是非常的好用的，大家都喜欢。", start_offset=0, end_offset=21),
    ]
    ctx = AgentContext(
        task_id="task1",
        rule_base_id="r1",
        rule_retriever=MockRuleRetriever(),
        doc_retriever=MockDocRetriever("task1"),
        llm=MockLLMClient(),
        publish_progress=lambda stage, pct, msg: None,
        config={"POLISH_ENABLED": "false"}
    )
    
    issues = agent.run(doc, spans, ctx)
    assert len(issues) == 0
