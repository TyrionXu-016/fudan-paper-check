from __future__ import annotations

import json
import os
from typing import Any

import httpx


class LLMClient:
    """OpenAI-compatible client (default: DeepSeek)."""

    def __init__(self) -> None:
        self.api_key = os.getenv("LLM_API_KEY") or os.getenv("OPENAI_API_KEY")
        self.base_url = os.getenv(
            "LLM_BASE_URL", os.getenv("OPENAI_BASE_URL", "https://api.deepseek.com/v1")
        )
        self.model = os.getenv("LLM_MODEL", "deepseek-chat")
        self.timeout = float(os.getenv("LLM_TIMEOUT_SEC", "90"))

    def is_available(self) -> bool:
        return bool(self.api_key)

    def complete_json(
        self,
        system: str,
        user: str,
        *,
        model: str | None = None,
        temperature: float = 0,
    ) -> dict[str, Any]:
        if not self.api_key:
            raise RuntimeError("LLM_API_KEY not configured")
        payload = {
            "model": model or self.model,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            "response_format": {"type": "json_object"},
            "temperature": temperature,
        }
        with httpx.Client(timeout=self.timeout) as client:
            resp = client.post(
                f"{self.base_url.rstrip('/')}/chat/completions",
                headers={"Authorization": f"Bearer {self.api_key}"},
                json=payload,
            )
            resp.raise_for_status()
            content = resp.json()["choices"][0]["message"]["content"]
            return json.loads(content)


llm_client = LLMClient()
