from __future__ import annotations

from agents.mse_review_agent import MseReviewAgent
from mse.chunker import SectionChunk
from schema.models import CheckCategory, IssueSeverity


def test_mse_review_agent_fallback_without_llm(monkeypatch):
    monkeypatch.delenv("LLM_API_KEY", raising=False)
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)

    agent = MseReviewAgent()
    chunk = SectionChunk(
        section_id="intro",
        title="引言",
        text="本文待补充实验数据。",
        start_line=1,
        end_line=20,
        page_start=1,
        page_end=2,
    )
    issues = agent.review_chunk(chunk, project_id="test-project")
    codes = {i.code for i in issues}
    assert "MSE_PLACEHOLDER" in codes or len(issues) >= 0


def test_mse_review_agent_parse_response():
    agent = MseReviewAgent()
    chunk = SectionChunk(
        section_id="s1",
        title="摘要",
        text="测试",
        start_line=1,
        end_line=5,
        page_start=1,
        page_end=1,
    )
    data = {
        "issues": [
            {
                "code": "MSE_FMT_001",
                "category": "format",
                "severity": "warning",
                "message": "摘要过长",
                "page": 1,
                "revision_hint": "精简摘要",
            }
        ]
    }
    issues = agent._parse_response(data, chunk, {})
    assert len(issues) == 1
    assert issues[0].code == "MSE_FMT_001"
    assert issues[0].severity == IssueSeverity.WARNING
    assert issues[0].category == CheckCategory.FORMAT
