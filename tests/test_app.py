from open_voice_box.app import build_controller
from open_voice_box.config import AppConfig
from open_voice_box.controller import ConversationController
from open_voice_box.llm.ollama import OllamaProvider


def test_build_controller_uses_ollama_for_default_config(monkeypatch):
    class FakeTranscriber:
        def __init__(self, model_name):
            self.model_name = model_name

    monkeypatch.setattr("open_voice_box.app.WhisperTranscriber", FakeTranscriber)
    controller = build_controller(AppConfig())

    assert isinstance(controller, ConversationController)
    assert isinstance(controller.provider, OllamaProvider)
    assert controller.transcriber.model_name == "small"
