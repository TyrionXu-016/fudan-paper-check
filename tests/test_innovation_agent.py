from __future__ import annotations

from agents.innovation_agent import InnovationAgent
from parser.fusion import DualSourceFusionParser


def test_innovation_agent_fallback(monkeypatch):
    monkeypatch.delenv("LLM_API_KEY", raising=False)
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)

    parser = DualSourceFusionParser()
    doc = parser.parse_files(
        "samples/基于集成深度学习模型的公路隧道交通流预测_钱超_maker.md",
        None,
    )
    result = InnovationAgent().analyze(doc)
    assert result["llm_summary"]
    assert 0 <= result["novelty_score"] <= 1
    assert result["suggested_questions_for_advisor"]


def test_build_innovation_review():
    from mse.innovation import build_innovation_review
    from parser.fusion import DualSourceFusionParser

    parser = DualSourceFusionParser()
    doc = parser.parse_files(
        "samples/基于集成深度学习模型的公路隧道交通流预测_钱超_maker.md",
        None,
    )
    review = build_innovation_review("proj-1", "round-1", doc)
    assert review.project_id == "proj-1"
    assert review.round_id == "round-1"
    assert review.llm_summary
