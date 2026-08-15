from open_voice_box.config import AppConfig


def test_defaults_to_local_ollama(monkeypatch):
    for key in (
        "OVB_PROVIDER",
        "OVB_OLLAMA_URL",
        "OVB_OLLAMA_MODEL",
        "OVB_OPENAI_MODEL",
        "OVB_STT_MODEL",
    ):
        monkeypatch.delenv(key, raising=False)

    config = AppConfig.from_env()

    assert config.provider == "ollama"
    assert config.ollama_url == "http://localhost:11434"
    assert config.ollama_model == "qwen3:4b-instruct"
    assert config.openai_model == "gpt-5-mini"
    assert config.stt_model == "small"


def test_environment_overrides_defaults(monkeypatch):
    monkeypatch.setenv("OVB_PROVIDER", "openai")
    monkeypatch.setenv("OVB_OLLAMA_MODEL", "gemma3:4b")
    monkeypatch.setenv("OVB_STT_MODEL", "base")

    config = AppConfig.from_env()

    assert config.provider == "openai"
    assert config.ollama_model == "gemma3:4b"
    assert config.stt_model == "base"


def test_invalid_provider_is_rejected(monkeypatch):
    monkeypatch.setenv("OVB_PROVIDER", "mystery")

    try:
        AppConfig.from_env()
    except ValueError as exc:
        assert "OVB_PROVIDER" in str(exc)
    else:
        raise AssertionError("Expected invalid provider to raise ValueError")
