from __future__ import annotations

import json
import os
from typing import Protocol, Callable, Any
from dataclasses import dataclass

from schema.models import PaperDocument, Span, Issue, DetectStage
from rag.rule_retriever import retrieve_rules, RuleSnippet


class LLMClient:
    def __init__(self):
        self.api_key = os.getenv("LLM_API_KEY", "")

    def chat(self, messages: list[dict], *, json_mode: bool = True, timeout: float = 60, model: str | None = None) -> str:
        if not self.api_key:
            return "[]"  # 优雅跳过无 API Key 的情况
        
        import requests
        base_url = os.getenv("LLM_BASE_URL", "https://api.modelarts-maas.com/openai/v1")
        model_name = model or os.getenv("LLM_BASE_MODEL", "Qwen2.5-72B-Instruct")

        url = f"{base_url.rstrip('/')}/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        payload = {
            "model": model_name,
            "messages": messages,
        }
        # ModelArts/OpenAI usually support response_format for json
        if json_mode:
            payload["response_format"] = {"type": "json_object"}
            
        try:
            resp = requests.post(url, json=payload, headers=headers, timeout=timeout)
            resp.raise_for_status()
            data = resp.json()
            return data["choices"][0]["message"]["content"]
        except Exception as e:
            print(f"LLM call failed: {e}")
            if "resp" in locals() and hasattr(resp, 'text'):
                print(f"Response: {resp.text}")
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
