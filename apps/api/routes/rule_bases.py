from __future__ import annotations

from fastapi import APIRouter, Depends, Query

from auth.service import get_current_user
from rag.rule_index import load_index
from rag.rule_retriever import RetrieveRulesResponse, retrieve_rules
from rule_bases.service import get_rule_base, list_rule_bases
from schema.api_response import (
    ERROR_RAG_INDEX_NOT_READY,
    ERROR_RULE_BASE_NOT_FOUND,
    ApiError,
    ApiResponse,
)
from schema.models import RuleBaseDetail, RuleBaseListItem
from storage.users import User

router = APIRouter(prefix="/v1/rule_bases", tags=["rule_bases"])


@router.get("")
async def list_all() -> ApiResponse[list[RuleBaseListItem]]:
    return ApiResponse.success(list_rule_bases())


@router.get("/{rule_base_id}")
async def get_one(rule_base_id: str) -> ApiResponse[RuleBaseDetail]:
    detail = get_rule_base(rule_base_id)
    if detail is None:
        raise ApiError(
            ERROR_RULE_BASE_NOT_FOUND,
            f"rule base not found: {rule_base_id}",
            status_code=404,
        )
    return ApiResponse.success(detail)


@router.get("/{rule_base_id}/retrieve")
async def retrieve_rule_snippets(
    rule_base_id: str,
    q: str = Query(..., min_length=1),
    top_k: int = Query(5, ge=1, le=20),
    user: User = Depends(get_current_user),
) -> ApiResponse[RetrieveRulesResponse]:
    if get_rule_base(rule_base_id) is None:
        raise ApiError(
            ERROR_RULE_BASE_NOT_FOUND,
            f"rule base not found: {rule_base_id}",
            status_code=404,
        )
    if load_index(rule_base_id) is None:
        raise ApiError(
            ERROR_RAG_INDEX_NOT_READY,
            f"RAG index is not ready for rule base: {rule_base_id}",
            status_code=503,
        )
    return ApiResponse.success(retrieve_rules(rule_base_id, q, top_k=top_k))
