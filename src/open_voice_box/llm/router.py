from open_voice_box.config import AppConfig
from open_voice_box.llm.base import LLMProvider
from open_voice_box.llm.ollama import OllamaProvider
from open_voice_box.llm.openai_api import OpenAIProvider


def build_provider(config: AppConfig) -> LLMProvider:
    if config.provider == "ollama":
        return OllamaProvider(config.ollama_url, config.ollama_model)
    if config.provider == "openai":
        return OpenAIProvider(config.openai_model)
    raise ValueError(f"Unsupported provider: {config.provider}")
