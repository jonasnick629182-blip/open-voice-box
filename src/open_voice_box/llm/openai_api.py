import os

from open_voice_box.errors import MissingCredentialError, ProviderUnavailableError
from open_voice_box.models import Message


class OpenAIProvider:
    def __init__(self, model: str, client=None):
        if not os.getenv("OPENAI_API_KEY"):
            raise MissingCredentialError(
                "OpenAI mode requires the OPENAI_API_KEY environment variable."
            )
        self.model = model
        self.client = client

    def _get_client(self):
        if self.client is not None:
            return self.client
        try:
            from openai import OpenAI
        except (ImportError, AttributeError) as exc:
            raise ProviderUnavailableError(
                "OpenAI support is not installed correctly. Reinstall project dependencies."
            ) from exc
        self.client = OpenAI()
        return self.client

    def generate(self, messages: list[Message]) -> str:
        try:
            response = self._get_client().responses.create(
                model=self.model,
                input=[{"role": m.role, "content": m.content} for m in messages],
            )
            text = response.output_text.strip()
        except ProviderUnavailableError:
            raise
        except Exception as exc:
            raise ProviderUnavailableError(
                "OpenAI request failed. Check the API key, model access, and network."
            ) from exc
        if not text:
            raise ProviderUnavailableError("OpenAI returned an empty response.")
        return text
