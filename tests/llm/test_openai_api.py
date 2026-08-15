import pytest

from open_voice_box.errors import MissingCredentialError, ProviderUnavailableError
from open_voice_box.llm.openai_api import OpenAIProvider
from open_voice_box.models import Message


class FakeResponse:
    output_text = "cloud reply"


class FakeResponses:
    def __init__(self):
        self.kwargs = None

    def create(self, **kwargs):
        self.kwargs = kwargs
        return FakeResponse()


class FakeClient:
    def __init__(self):
        self.responses = FakeResponses()


def test_openai_provider_uses_responses_api(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    client = FakeClient()
    provider = OpenAIProvider("gpt-5-mini", client=client)

    result = provider.generate([Message("user", "hello")])

    assert result == "cloud reply"
    assert client.responses.kwargs == {
        "model": "gpt-5-mini",
        "input": [{"role": "user", "content": "hello"}],
    }


def test_openai_provider_requires_key(monkeypatch):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    with pytest.raises(MissingCredentialError, match="OPENAI_API_KEY"):
        OpenAIProvider("gpt-5-mini")


def test_openai_errors_are_normalized(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")

    class BrokenResponses:
        def create(self, **kwargs):
            raise RuntimeError("network failed")

    class BrokenClient:
        responses = BrokenResponses()

    provider = OpenAIProvider("gpt-5-mini", client=BrokenClient())
    with pytest.raises(ProviderUnavailableError, match="OpenAI"):
        provider.generate([Message("user", "hello")])
