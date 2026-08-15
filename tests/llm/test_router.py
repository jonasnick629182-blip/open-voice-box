from open_voice_box.config import AppConfig
from open_voice_box.llm.ollama import OllamaProvider
from open_voice_box.llm.openai_api import OpenAIProvider
from open_voice_box.llm.router import build_provider


def test_router_builds_ollama_by_default():
    provider = build_provider(AppConfig())
    assert isinstance(provider, OllamaProvider)


def test_router_builds_openai(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    provider = build_provider(AppConfig(provider="openai"))
    assert isinstance(provider, OpenAIProvider)
