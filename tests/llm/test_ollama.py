import httpx
import pytest

from open_voice_box.errors import MissingModelError, ProviderUnavailableError
from open_voice_box.llm.ollama import OllamaProvider
from open_voice_box.models import Message


def test_ollama_sends_non_streaming_non_thinking_chat():
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/api/chat"
        payload = __import__("json").loads(request.content)
        assert payload["model"] == "qwen3:4b-instruct"
        assert payload["stream"] is False
        assert payload["think"] is False
        assert payload["messages"] == [{"role": "user", "content": "你好"}]
        return httpx.Response(200, json={"message": {"role": "assistant", "content": "你好！"}})

    client = httpx.Client(transport=httpx.MockTransport(handler))
    provider = OllamaProvider("http://localhost:11434", "qwen3:4b-instruct", client=client)

    assert provider.generate([Message("user", "你好")]) == "你好！"


def test_ollama_404_becomes_missing_model():
    client = httpx.Client(transport=httpx.MockTransport(lambda _: httpx.Response(404, text="not found")))
    provider = OllamaProvider("http://localhost:11434", "missing", client=client)

    with pytest.raises(MissingModelError, match="ollama pull missing"):
        provider.generate([Message("user", "hi")])


def test_ollama_connection_error_becomes_friendly_error():
    def handler(_: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("offline")

    client = httpx.Client(transport=httpx.MockTransport(handler))
    provider = OllamaProvider("http://localhost:11434", "qwen3:4b-instruct", client=client)

    with pytest.raises(ProviderUnavailableError, match="Ollama"):
        provider.generate([Message("user", "hi")])
