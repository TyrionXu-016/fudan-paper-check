import pytest
from agents.model_router import ModelRouter
import os

def test_model_router_fallback(monkeypatch):
    monkeypatch.setenv("FT_ENABLED", "false")
    monkeypatch.setenv("LLM_API_KEY", "dummy")
    monkeypatch.setenv("FT_ADAPTER_TYPO", "lora-typo-v1")
    
    router = ModelRouter()
    # Mock super().chat to return model used (since we'll modify it later to pass model)
    # Since we haven't modified LLMClient yet, it just returns "[]"
    res = router.chat([], task_type="typo")
    assert res == "[]"

def test_model_router_ft_enabled(monkeypatch):
    monkeypatch.setenv("FT_ENABLED", "true")
    monkeypatch.setenv("LLM_API_KEY", "dummy")
    monkeypatch.setenv("FT_ADAPTER_TYPO", "lora-typo-v1")
    
    router = ModelRouter()
    res = router.chat([], task_type="typo")
    assert res == "[]"
