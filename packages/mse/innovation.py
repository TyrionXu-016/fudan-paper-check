from __future__ import annotations

import uuid

from agents.innovation_agent import InnovationAgent
from mse.models import InnovationReview
from schema.models import PaperDocument
from storage.users import now_iso


def build_innovation_review(
    project_id: str,
    round_id: str,
    doc: PaperDocument,
) -> InnovationReview:
    agent = InnovationAgent()
    data = agent.analyze(doc)
    return InnovationReview(
        id=str(uuid.uuid4()),
        project_id=project_id,
        round_id=round_id,
        llm_summary=str(data.get("llm_summary") or ""),
        novelty_score=_as_float(data.get("novelty_score")),
        comparison_notes=str(data.get("comparison_notes") or ""),
        strengths=_as_str_list(data.get("strengths")),
        weaknesses=_as_str_list(data.get("weaknesses")),
        suggested_questions=_as_str_list(data.get("suggested_questions_for_advisor")),
        created_at=now_iso(),
    )


def _as_float(value) -> float | None:
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _as_str_list(value) -> list[str]:
    if not isinstance(value, list):
        return []
    return [str(v) for v in value if v]
