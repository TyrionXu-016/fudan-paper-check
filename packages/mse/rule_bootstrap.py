from __future__ import annotations

import logging
import uuid

from fastapi import HTTPException

from mse.models import TutoringProject
from rag.mse_rule_index import build_project_index, load_project_index

logger = logging.getLogger(__name__)


def bootstrap_project_default_rules(project_id: str, repo) -> TutoringProject:
    """Build default MSE rule RAG index and attach a rule_base_id to the project."""
    build_project_index(project_id, include_default=True)
    index = load_project_index(project_id)
    chunk_count = (index or {}).get("chunk_count", 0)
    if chunk_count <= 0:
        logger.error("default rule index empty for project %s", project_id)
        raise HTTPException(500, "failed to index default rule documents")
    rule_id = f"rule-default-{uuid.uuid4().hex[:8]}"
    return repo.add_rule_document(project_id, rule_id)
