import httpx

from open_voice_box.errors import MissingModelError, ProviderUnavailableError
from open_voice_box.models import Message


class OllamaProvider:
    def __init__(self, base_url: str, model: str, client: httpx.Client | None = None):
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.client = client or httpx.Client(timeout=60.0)

    def generate(self, messages: list[Message]) -> str:
        payload = {
            "model": self.model,
            "messages": [{"role": m.role, "content": m.content} for m in messages],
            "stream": False,
            "think": False,
        }
        try:
            response = self.client.post(f"{self.base_url}/api/chat", json=payload)
        except httpx.HTTPError as exc:
            raise ProviderUnavailableError(
                "Ollama is not reachable. Start Ollama and try again."
            ) from exc
        if response.status_code == 404:
            raise MissingModelError(
                f"Ollama model '{self.model}' is missing. Run: ollama pull {self.model}"
            )
        try:
            response.raise_for_status()
            text = response.json()["message"]["content"].strip()
        except (httpx.HTTPError, KeyError, TypeError, ValueError) as exc:
            raise ProviderUnavailableError("Ollama returned an invalid response.") from exc
        if not text:
            raise ProviderUnavailableError("Ollama returned an empty response.")
        return text
