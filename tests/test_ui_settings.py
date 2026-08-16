from open_voice_box.config import AppConfig
from open_voice_box.ui.main_window import with_provider_settings


def test_ollama_model_setting_updates_only_local_model():
    config = with_provider_settings(AppConfig(), "ollama", "gemma3:4b")
    assert config.provider == "ollama"
    assert config.ollama_model == "gemma3:4b"
    assert config.openai_model == "gpt-5-mini"


def test_openai_model_setting_updates_only_cloud_model():
    config = with_provider_settings(AppConfig(), "openai", "gpt-5.1-mini")
    assert config.provider == "openai"
    assert config.openai_model == "gpt-5.1-mini"
    assert config.ollama_model == "qwen3:4b-instruct"
