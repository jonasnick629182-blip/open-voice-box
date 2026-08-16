from dataclasses import dataclass
import os

from dotenv import load_dotenv


@dataclass(frozen=True)
class AppConfig:
    provider: str = "ollama"
    ollama_url: str = "http://localhost:11434"
    ollama_model: str = "qwen3:4b-instruct"
    openai_model: str = "gpt-5-mini"
    stt_model: str = "small"
    tts_voice: str | None = None

    @classmethod
    def from_env(cls) -> "AppConfig":
        load_dotenv()
        provider = os.getenv("OVB_PROVIDER", "ollama").strip().lower()
        if provider not in {"ollama", "openai"}:
            raise ValueError("OVB_PROVIDER must be 'ollama' or 'openai'")
        voice = os.getenv("OVB_TTS_VOICE", "").strip() or None
        return cls(
            provider=provider,
            ollama_url=os.getenv("OVB_OLLAMA_URL", "http://localhost:11434").rstrip("/"),
            ollama_model=os.getenv("OVB_OLLAMA_MODEL", "qwen3:4b-instruct"),
            openai_model=os.getenv("OVB_OPENAI_MODEL", "gpt-5-mini"),
            stt_model=os.getenv("OVB_STT_MODEL", "small"),
            tts_voice=voice,
        )
