from typing import Protocol

from open_voice_box.models import Message


class LLMProvider(Protocol):
    def generate(self, messages: list[Message]) -> str: ...
