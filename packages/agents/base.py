from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Protocol, Callable, Any

from schema.models import PaperDocument, Span, Issue, DetectStage
from rag.rule_retriever import retrieve_rules, RuleSnippet


class LLMClient:
    def chat(self, messages: list[dict], *, json_mode: bool = True, timeout: float = 60) -> str:
        # MVP Mock LLM Client
        return "[]"


class ModelRouter(LLMClient):
    pass


class RuleRetriever:
    def __init__(self, rule_base_id: str):
        self.rule_base_id = rule_base_id

    def retrieve(self, query: str, *, dimensions: list[str] | None = None, top_k: int = 5) -> list[RuleSnippet]:
        resp = retrieve_rules(self.rule_base_id, query, top_k=top_k, dimensions=dimensions)
        return resp.results


class DocRetriever:
    def __init__(self, task_id: str):
        self.task_id = task_id


@dataclass
class AgentContext:
    task_id: str
    rule_base_id: str
    rule_retriever: RuleRetriever
    doc_retriever: DocRetriever
    llm: LLMClient | ModelRouter
    publish_progress: Callable[[DetectStage, int, str], None]
    config: dict[str, Any]


class BaseAgent(Protocol):
    name: str
    stage: DetectStage

    def run(self, doc: PaperDocument, spans: list[Span], ctx: AgentContext) -> list[Issue]:
        ...
