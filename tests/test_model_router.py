from agents.model_router import ModelRouter
from agents.base import LLMClient

def test_model_router_fallback(monkeypatch):
    monkeypatch.setenv("FT_ENABLED", "false")
    monkeypatch.setenv("LLM_API_KEY", "dummy")
    monkeypatch.setenv("LLM_BASE_MODEL", "base-model")
    monkeypatch.setenv("FT_ADAPTER_TYPO", "lora-typo-v1")

    calls = []

    def fake_chat(self, messages, *, model=None, **kwargs):
        calls.append(model)
        return '{"issues": []}'

    monkeypatch.setattr(LLMClient, "chat", fake_chat)

    router = ModelRouter()
    res = router.chat([], task_type="typo")
    assert res == '{"issues": []}'
    assert calls == ["base-model"]

def test_model_router_ft_enabled(monkeypatch):
    monkeypatch.setenv("FT_ENABLED", "true")
    monkeypatch.setenv("LLM_API_KEY", "dummy")
    monkeypatch.setenv("LLM_BASE_MODEL", "base-model")
    monkeypatch.setenv("FT_ADAPTER_TYPO", "lora-typo-v1")

    calls = []

    def fake_chat(self, messages, *, model=None, **kwargs):
        calls.append(model)
        return '{"issues": []}'

    monkeypatch.setattr(LLMClient, "chat", fake_chat)

    router = ModelRouter()
    res = router.chat([], task_type="typo")
    assert res == '{"issues": []}'
    assert calls == ["lora-typo-v1"]
