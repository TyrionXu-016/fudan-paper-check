from __future__ import annotations

import os
from typing import Any

from agents.base import LLMClient


class ModelRouter(LLMClient):
    """
    Routes LLM requests to specific fine-tuned LoRA adapters based on the task type,
    if fine-tuning is enabled. Otherwise falls back to the base model.
    """
    def __init__(self):
        super().__init__()
        self.ft_enabled = os.getenv("FT_ENABLED", "false").lower() == "true"
        self.base_model = os.getenv("LLM_BASE_MODEL", "qwen-plus")
        self.adapters = {
            "typo": os.getenv("FT_ADAPTER_TYPO", ""),
            "grammar": os.getenv("FT_ADAPTER_TYPO", ""),
            "polish": os.getenv("FT_ADAPTER_POLISH", ""),
            "paragraph_logic": os.getenv("FT_ADAPTER_POLISH", ""),
            "sentence_split": os.getenv("FT_ADAPTER_POLISH", ""),
            "logic_contradiction": os.getenv("FT_ADAPTER_LOGIC", ""),
        }

    def chat(self, messages: list[dict], *, json_mode: bool = True, timeout: float = 60, task_type: str = "") -> str:
        adapter = self.adapters.get(task_type, "")
        
        if self.ft_enabled and adapter:
            # Here we would inject the adapter parameter to the actual LLM client call
            # e.g. return super().chat(messages, model=adapter, ...)
            pass
            
        return super().chat(messages, json_mode=json_mode, timeout=timeout)
