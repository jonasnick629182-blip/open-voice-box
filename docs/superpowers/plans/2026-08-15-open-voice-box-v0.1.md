# Open Voice Box V0.1 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a macOS-first bilingual push-to-talk desktop voice companion that works with a free local Ollama model by default and can optionally use the OpenAI API.

**Architecture:** A thin Tkinter UI calls a conversation controller. The controller coordinates four isolated capabilities: microphone recording, local speech-to-text, provider-neutral LLM generation, and text-to-speech. Provider-specific code lives behind one interface so Ollama and OpenAI can be switched through configuration without changing application logic.

**Tech Stack:** Python 3.11+, Tkinter, sounddevice, soundfile, NumPy, faster-whisper, httpx, OpenAI Python SDK, python-dotenv, pytest.

## Global Constraints

- Python version floor: Python 3.11+.
- macOS-first V0.1; Linux and Raspberry Pi are future compatibility targets, not release blockers.
- Interaction model: one-button push-to-talk; no wake word and no always-on listening.
- Speech input: Chinese and English, auto-detected locally.
- Default LLM path: Ollama on `http://localhost:11434`.
- Default local model: `qwen3:4b-instruct`; requests disable thinking for low-latency voice chat.
- Optional cloud provider: OpenAI Responses API using `OPENAI_API_KEY`.
- No API keys, tokens, recordings, or local `.env` files may be committed.
- V0.1 session history is memory-only; no persistent memory.
- Heavy transcription/model work must not block the Tkinter UI thread.
- A TTS failure must not hide or discard the assistant's text response.

---

## File Map

Files created by this plan and their single responsibilities:

```text
pyproject.toml                         Packaging, dependencies, test configuration
.env.example                          Non-secret configuration example
.gitignore                            Ignore secrets/cache/temp audio
src/open_voice_box/__init__.py        Package metadata
src/open_voice_box/errors.py          User-facing domain exceptions
src/open_voice_box/models.py          Message/transcript/state data types
src/open_voice_box/config.py          Environment/config parsing
src/open_voice_box/llm/base.py        LLM provider protocol
src/open_voice_box/llm/ollama.py      Ollama HTTP implementation
src/open_voice_box/llm/openai_api.py  OpenAI Responses API implementation
src/open_voice_box/llm/router.py      Provider selection
src/open_voice_box/audio/recorder.py  Push-to-talk microphone capture
src/open_voice_box/stt/whisper.py     faster-whisper transcription
src/open_voice_box/tts/macos.py       macOS `say` speech output
src/open_voice_box/controller.py      Conversation state machine/orchestration
src/open_voice_box/ui/main_window.py  Tkinter rendering and user interaction
src/open_voice_box/app.py             Dependency wiring and entry point
src/open_voice_box/__main__.py        `python -m open_voice_box` entry point

tests/test_config.py                  Configuration behavior
tests/llm/test_ollama.py              Ollama request/error behavior
tests/llm/test_openai_api.py          OpenAI request/error behavior
tests/llm/test_router.py              Provider routing
tests/audio/test_recorder.py          Recorder lifecycle/error behavior
tests/stt/test_whisper.py             STT normalization/error behavior
tests/tts/test_macos.py               TTS command/error behavior
tests/test_controller.py              End-to-end orchestration with fakes
tests/test_app.py                     Dependency wiring smoke test

README.md                              English project/setup docs
README_CN.md                           Chinese project/setup docs
CONTRIBUTING.md                        Contribution workflow
SECURITY.md                            Security reporting guidance
CHANGELOG.md                           Release history
LICENSE                               MIT license
.github/workflows/ci.yml               Automated unit tests
.github/ISSUE_TEMPLATE/bug_report.yml  Structured bug reports
.github/ISSUE_TEMPLATE/feature_request.yml  Structured feature requests
```

---

### Task 1: Package foundation, shared types, and configuration

**Files:**
- Create: `pyproject.toml`
- Create: `.gitignore`
- Create: `.env.example`
- Create: `src/open_voice_box/__init__.py`
- Create: `src/open_voice_box/errors.py`
- Create: `src/open_voice_box/models.py`
- Create: `src/open_voice_box/config.py`
- Test: `tests/test_config.py`

**Interfaces:**
- Produces: `AppConfig.from_env() -> AppConfig`
- Produces: `Message(role: Literal["user", "assistant"], content: str)`
- Produces: `TurnResult(user_text: str, assistant_text: str, language: str | None)`
- Produces: domain exceptions imported by every later task.

- [ ] **Step 1: Write the failing configuration tests**

Create `tests/test_config.py`:

```python
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
```

- [ ] **Step 2: Run the test and verify it fails**

Run:

```bash
python -m pytest tests/test_config.py -v
```

Expected: FAIL during import because the package/config module does not exist yet.

- [ ] **Step 3: Create packaging and minimal implementation**

Create `pyproject.toml`:

```toml
[build-system]
requires = ["setuptools>=68", "wheel"]
build-backend = "setuptools.build_meta"

[project]
name = "open-voice-box"
version = "0.1.0"
description = "Local-first bilingual voice AI companion"
readme = "README.md"
requires-python = ">=3.11"
license = {text = "MIT"}
dependencies = [
  "faster-whisper",
  "httpx",
  "numpy",
  "openai",
  "python-dotenv",
  "sounddevice",
  "soundfile",
]

[project.optional-dependencies]
dev = ["pytest"]

[project.scripts]
open-voice-box = "open_voice_box.app:main"

[tool.setuptools.packages.find]
where = ["src"]

[tool.pytest.ini_options]
pythonpath = ["src"]
testpaths = ["tests"]
```

Create `.gitignore`:

```gitignore
.venv/
.env
__pycache__/
*.py[cod]
.pytest_cache/
.DS_Store
*.wav
*.aiff
*.mp3
build/
dist/
*.egg-info/
```

Create `.env.example`:

```dotenv
OVB_PROVIDER=ollama
OVB_OLLAMA_URL=http://localhost:11434
OVB_OLLAMA_MODEL=qwen3:4b-instruct
OVB_OPENAI_MODEL=gpt-5-mini
OVB_STT_MODEL=small
OVB_TTS_VOICE=
OPENAI_API_KEY=
```

Create `src/open_voice_box/__init__.py`:

```python
__version__ = "0.1.0"
```

Create `src/open_voice_box/errors.py`:

```python
class OpenVoiceBoxError(Exception):
    """Base error that can be shown to a user."""


class AudioInputError(OpenVoiceBoxError):
    pass


class TranscriptionError(OpenVoiceBoxError):
    pass


class ProviderUnavailableError(OpenVoiceBoxError):
    pass


class MissingModelError(OpenVoiceBoxError):
    pass


class MissingCredentialError(OpenVoiceBoxError):
    pass


class SpeechError(OpenVoiceBoxError):
    pass
```

Create `src/open_voice_box/models.py`:

```python
from dataclasses import dataclass
from typing import Literal


Role = Literal["user", "assistant"]


@dataclass(frozen=True)
class Message:
    role: Role
    content: str


@dataclass(frozen=True)
class TurnResult:
    user_text: str
    assistant_text: str
    language: str | None
```

Create `src/open_voice_box/config.py`:

```python
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
```

- [ ] **Step 4: Install the editable package and run tests**

Run:

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -e '.[dev]'
python -m pytest tests/test_config.py -v
```

Expected: 3 tests PASS.

- [ ] **Step 5: Commit**

```bash
git add pyproject.toml .gitignore .env.example src/open_voice_box tests/test_config.py
git commit -m "chore: establish project foundation"
```

---

### Task 2: Provider-neutral LLM layer with Ollama and OpenAI

**Files:**
- Create: `src/open_voice_box/llm/__init__.py`
- Create: `src/open_voice_box/llm/base.py`
- Create: `src/open_voice_box/llm/ollama.py`
- Create: `src/open_voice_box/llm/openai_api.py`
- Create: `src/open_voice_box/llm/router.py`
- Test: `tests/llm/test_ollama.py`
- Test: `tests/llm/test_openai_api.py`
- Test: `tests/llm/test_router.py`

**Interfaces:**
- Consumes: `Message`, `AppConfig`, provider exceptions.
- Produces: `LLMProvider.generate(messages: list[Message]) -> str`.
- Produces: `build_provider(config: AppConfig) -> LLMProvider`.

- [ ] **Step 1: Write failing provider tests**

Create `tests/llm/test_ollama.py`:

```python
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
```

Create `tests/llm/test_openai_api.py`:

```python
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
```

Create `tests/llm/test_router.py`:

```python
from open_voice_box.config import AppConfig
from open_voice_box.llm.ollama import OllamaProvider
from open_voice_box.llm.openai_api import OpenAIProvider
from open_voice_box.llm.router import build_provider


def test_router_builds_ollama_by_default():
    provider = build_provider(AppConfig())
    assert isinstance(provider, OllamaProvider)


def test_router_builds_openai(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    provider = build_provider(AppConfig(provider="openai"))
    assert isinstance(provider, OpenAIProvider)
```

- [ ] **Step 2: Run provider tests and verify failure**

```bash
python -m pytest tests/llm -v
```

Expected: FAIL because `open_voice_box.llm` does not exist.

- [ ] **Step 3: Implement provider protocol and providers**

Create `src/open_voice_box/llm/base.py`:

```python
from typing import Protocol

from open_voice_box.models import Message


class LLMProvider(Protocol):
    def generate(self, messages: list[Message]) -> str: ...
```

Create empty `src/open_voice_box/llm/__init__.py`.

Create `src/open_voice_box/llm/ollama.py`:

```python
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
```

Create `src/open_voice_box/llm/openai_api.py`:

```python
import os

from openai import OpenAI

from open_voice_box.errors import MissingCredentialError, ProviderUnavailableError
from open_voice_box.models import Message


class OpenAIProvider:
    def __init__(self, model: str, client=None):
        if not os.getenv("OPENAI_API_KEY"):
            raise MissingCredentialError(
                "OpenAI mode requires the OPENAI_API_KEY environment variable."
            )
        self.model = model
        self.client = client or OpenAI()

    def generate(self, messages: list[Message]) -> str:
        try:
            response = self.client.responses.create(
                model=self.model,
                input=[{"role": m.role, "content": m.content} for m in messages],
            )
            text = response.output_text.strip()
        except Exception as exc:
            raise ProviderUnavailableError(
                "OpenAI request failed. Check the API key, model access, and network."
            ) from exc
        if not text:
            raise ProviderUnavailableError("OpenAI returned an empty response.")
        return text
```

Create `src/open_voice_box/llm/router.py`:

```python
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
```

- [ ] **Step 4: Run provider tests**

```bash
python -m pytest tests/llm -v
```

Expected: all provider tests PASS.

- [ ] **Step 5: Commit**

```bash
git add src/open_voice_box/llm tests/llm
git commit -m "feat: add local and cloud llm providers"
```

---

### Task 3: Push-to-talk microphone recorder

**Files:**
- Create: `src/open_voice_box/audio/__init__.py`
- Create: `src/open_voice_box/audio/recorder.py`
- Test: `tests/audio/test_recorder.py`

**Interfaces:**
- Produces: `PushToTalkRecorder.start() -> None`
- Produces: `PushToTalkRecorder.stop() -> Path`
- `stop()` returns a temporary mono 16 kHz WAV file path suitable for STT.

- [ ] **Step 1: Write failing recorder tests**

Create `tests/audio/test_recorder.py`:

```python
from pathlib import Path
import numpy as np
import pytest

from open_voice_box.audio.recorder import PushToTalkRecorder
from open_voice_box.errors import AudioInputError


class FakeStream:
    def __init__(self, callback):
        self.callback = callback
        self.started = False
        self.stopped = False

    def start(self):
        self.started = True
        self.callback(np.ones((160, 1), dtype=np.float32), 160, None, None)

    def stop(self):
        self.stopped = True

    def close(self):
        pass


def test_start_then_stop_writes_wav(monkeypatch, tmp_path):
    created = {}

    def fake_input_stream(**kwargs):
        created["stream"] = FakeStream(kwargs["callback"])
        return created["stream"]

    written = {}

    def fake_write(path, audio, samplerate):
        written["path"] = Path(path)
        written["audio"] = audio
        written["samplerate"] = samplerate

    monkeypatch.setattr("open_voice_box.audio.recorder.sd.InputStream", fake_input_stream)
    monkeypatch.setattr("open_voice_box.audio.recorder.sf.write", fake_write)

    recorder = PushToTalkRecorder(temp_dir=tmp_path)
    recorder.start()
    path = recorder.stop()

    assert path.suffix == ".wav"
    assert written["samplerate"] == 16000
    assert written["audio"].shape == (160, 1)
    assert created["stream"].stopped is True


def test_stop_without_audio_raises(monkeypatch, tmp_path):
    class SilentStream(FakeStream):
        def start(self):
            self.started = True

    monkeypatch.setattr(
        "open_voice_box.audio.recorder.sd.InputStream",
        lambda **kwargs: SilentStream(kwargs["callback"]),
    )

    recorder = PushToTalkRecorder(temp_dir=tmp_path)
    recorder.start()
    with pytest.raises(AudioInputError, match="No audio"):
        recorder.stop()
```

- [ ] **Step 2: Run and verify failure**

```bash
python -m pytest tests/audio/test_recorder.py -v
```

Expected: FAIL because recorder module is missing.

- [ ] **Step 3: Implement arbitrary-duration recording with an InputStream**

Create empty `src/open_voice_box/audio/__init__.py`.

Create `src/open_voice_box/audio/recorder.py`:

```python
from pathlib import Path
import tempfile
import threading

import numpy as np
import sounddevice as sd
import soundfile as sf

from open_voice_box.errors import AudioInputError


class PushToTalkRecorder:
    def __init__(self, samplerate: int = 16000, channels: int = 1, temp_dir: Path | None = None):
        self.samplerate = samplerate
        self.channels = channels
        self.temp_dir = temp_dir
        self._stream = None
        self._chunks: list[np.ndarray] = []
        self._lock = threading.Lock()

    def _callback(self, indata, frames, time, status):
        if status:
            # Status is diagnostic; keep recording unless PortAudio itself raises.
            pass
        with self._lock:
            self._chunks.append(indata.copy())

    def start(self) -> None:
        if self._stream is not None:
            return
        self._chunks = []
        try:
            self._stream = sd.InputStream(
                samplerate=self.samplerate,
                channels=self.channels,
                dtype="float32",
                callback=self._callback,
            )
            self._stream.start()
        except Exception as exc:
            self._stream = None
            raise AudioInputError(
                "Microphone could not be opened. Check macOS microphone permission and input device settings."
            ) from exc

    def stop(self) -> Path:
        stream = self._stream
        self._stream = None
        if stream is not None:
            try:
                stream.stop()
                stream.close()
            except Exception:
                pass
        with self._lock:
            chunks = list(self._chunks)
            self._chunks = []
        if not chunks:
            raise AudioInputError("No audio was recorded. Please try again.")
        audio = np.concatenate(chunks, axis=0)
        handle = tempfile.NamedTemporaryFile(
            suffix=".wav", delete=False, dir=self.temp_dir
        )
        path = Path(handle.name)
        handle.close()
        sf.write(path, audio, self.samplerate)
        return path
```

- [ ] **Step 4: Run recorder tests**

```bash
python -m pytest tests/audio/test_recorder.py -v
```

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add src/open_voice_box/audio tests/audio
git commit -m "feat: add push to talk recorder"
```

---

### Task 4: Local bilingual speech-to-text

**Files:**
- Create: `src/open_voice_box/stt/__init__.py`
- Create: `src/open_voice_box/stt/whisper.py`
- Test: `tests/stt/test_whisper.py`

**Interfaces:**
- Produces: `Transcription(text: str, language: str | None)`.
- Produces: `WhisperTranscriber.transcribe(path: Path) -> Transcription`.

- [ ] **Step 1: Write failing transcription tests**

Create `tests/stt/test_whisper.py`:

```python
from pathlib import Path
import pytest

from open_voice_box.errors import TranscriptionError
from open_voice_box.stt.whisper import WhisperTranscriber


class Segment:
    def __init__(self, text):
        self.text = text


class Info:
    language = "zh"


class FakeModel:
    def transcribe(self, path, **kwargs):
        assert kwargs["language"] is None
        assert kwargs["vad_filter"] is True
        return iter([Segment(" 你好 "), Segment(" 世界 ")]), Info()


def test_transcribe_joins_segments_and_returns_language():
    transcriber = WhisperTranscriber("small", model=FakeModel())
    result = transcriber.transcribe(Path("sample.wav"))
    assert result.text == "你好 世界"
    assert result.language == "zh"


class EmptyModel:
    def transcribe(self, path, **kwargs):
        return iter([]), Info()


def test_empty_transcript_is_rejected():
    transcriber = WhisperTranscriber("small", model=EmptyModel())
    with pytest.raises(TranscriptionError, match="understand"):
        transcriber.transcribe(Path("sample.wav"))
```

- [ ] **Step 2: Run and verify failure**

```bash
python -m pytest tests/stt/test_whisper.py -v
```

Expected: FAIL because STT module is missing.

- [ ] **Step 3: Implement faster-whisper wrapper**

Create empty `src/open_voice_box/stt/__init__.py`.

Create `src/open_voice_box/stt/whisper.py`:

```python
from dataclasses import dataclass
from pathlib import Path

from faster_whisper import WhisperModel

from open_voice_box.errors import TranscriptionError


@dataclass(frozen=True)
class Transcription:
    text: str
    language: str | None


class WhisperTranscriber:
    def __init__(self, model_name: str = "small", model=None):
        try:
            self.model = model or WhisperModel(
                model_name,
                device="cpu",
                compute_type="int8",
            )
        except Exception as exc:
            raise TranscriptionError(
                "Speech model could not be loaded. Check the network on first run and try again."
            ) from exc

    def transcribe(self, path: Path) -> Transcription:
        try:
            segments, info = self.model.transcribe(
                str(path),
                language=None,
                vad_filter=True,
                condition_on_previous_text=False,
            )
            text = " ".join(segment.text.strip() for segment in segments if segment.text.strip()).strip()
        except Exception as exc:
            raise TranscriptionError("Speech transcription failed. Please try again.") from exc
        if not text:
            raise TranscriptionError("I could not understand any speech. Please try again.")
        return Transcription(text=text, language=getattr(info, "language", None))
```

- [ ] **Step 4: Run STT tests**

```bash
python -m pytest tests/stt/test_whisper.py -v
```

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add src/open_voice_box/stt tests/stt
git commit -m "feat: add bilingual local transcription"
```

---

### Task 5: macOS local text-to-speech

**Files:**
- Create: `src/open_voice_box/tts/__init__.py`
- Create: `src/open_voice_box/tts/macos.py`
- Test: `tests/tts/test_macos.py`

**Interfaces:**
- Produces: `MacSpeaker.speak(text: str) -> None`.
- Optional configured voice is passed to macOS `say`; otherwise the system default voice is used.

- [ ] **Step 1: Write failing speaker tests**

Create `tests/tts/test_macos.py`:

```python
import subprocess
import pytest

from open_voice_box.errors import SpeechError
from open_voice_box.tts.macos import MacSpeaker


def test_speaker_uses_system_default_when_voice_missing(monkeypatch):
    calls = []
    monkeypatch.setattr(subprocess, "run", lambda args, **kwargs: calls.append((args, kwargs)))

    MacSpeaker().speak("你好 hello")

    assert calls[0][0] == ["say", "你好 hello"]
    assert calls[0][1]["check"] is True


def test_speaker_uses_configured_voice(monkeypatch):
    calls = []
    monkeypatch.setattr(subprocess, "run", lambda args, **kwargs: calls.append(args))

    MacSpeaker("Tingting").speak("你好")

    assert calls[0] == ["say", "-v", "Tingting", "你好"]


def test_speaker_failure_is_normalized(monkeypatch):
    def fail(*args, **kwargs):
        raise subprocess.CalledProcessError(1, "say")

    monkeypatch.setattr(subprocess, "run", fail)
    with pytest.raises(SpeechError, match="spoken"):
        MacSpeaker().speak("hello")
```

- [ ] **Step 2: Run and verify failure**

```bash
python -m pytest tests/tts/test_macos.py -v
```

Expected: FAIL because TTS module is missing.

- [ ] **Step 3: Implement the macOS speaker**

Create empty `src/open_voice_box/tts/__init__.py`.

Create `src/open_voice_box/tts/macos.py`:

```python
import subprocess

from open_voice_box.errors import SpeechError


class MacSpeaker:
    def __init__(self, voice: str | None = None):
        self.voice = voice

    def speak(self, text: str) -> None:
        if not text.strip():
            return
        command = ["say"]
        if self.voice:
            command.extend(["-v", self.voice])
        command.append(text)
        try:
            subprocess.run(command, check=True)
        except (FileNotFoundError, subprocess.CalledProcessError) as exc:
            raise SpeechError(
                "The answer was generated, but it could not be spoken aloud."
            ) from exc
```

- [ ] **Step 4: Run TTS tests**

```bash
python -m pytest tests/tts/test_macos.py -v
```

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add src/open_voice_box/tts tests/tts
git commit -m "feat: add local macos speech output"
```

---

### Task 6: Conversation controller and recoverable state flow

**Files:**
- Create: `src/open_voice_box/controller.py`
- Test: `tests/test_controller.py`

**Interfaces:**
- Consumes: recorder, transcriber, LLM provider, speaker.
- Produces: `ConversationController.start_recording() -> None`.
- Produces: `ConversationController.finish_turn() -> TurnResult`.
- Produces: `ConversationController.history: list[Message]` for memory-only session context.
- Speaker failures are swallowed after text generation; all earlier failures are propagated as domain errors.

- [ ] **Step 1: Write failing controller tests**

Create `tests/test_controller.py`:

```python
from pathlib import Path

from open_voice_box.controller import ConversationController
from open_voice_box.errors import SpeechError, TranscriptionError
from open_voice_box.models import Message
from open_voice_box.stt.whisper import Transcription


class FakeRecorder:
    def __init__(self):
        self.started = False

    def start(self):
        self.started = True

    def stop(self):
        return Path("turn.wav")


class FakeTranscriber:
    def transcribe(self, path):
        return Transcription("你好", "zh")


class FakeProvider:
    def __init__(self):
        self.messages = None

    def generate(self, messages):
        self.messages = messages
        return "你好，有什么可以帮你？"


class FakeSpeaker:
    def __init__(self, fail=False):
        self.text = None
        self.fail = fail

    def speak(self, text):
        self.text = text
        if self.fail:
            raise SpeechError("speaker failed")


def test_full_turn_updates_history_and_speaks():
    recorder = FakeRecorder()
    provider = FakeProvider()
    speaker = FakeSpeaker()
    controller = ConversationController(recorder, FakeTranscriber(), provider, speaker)

    controller.start_recording()
    result = controller.finish_turn()

    assert recorder.started is True
    assert result.user_text == "你好"
    assert result.assistant_text == "你好，有什么可以帮你？"
    assert result.language == "zh"
    assert controller.history == [
        Message("user", "你好"),
        Message("assistant", "你好，有什么可以帮你？"),
    ]
    assert provider.messages == [Message("user", "你好")]
    assert speaker.text == "你好，有什么可以帮你？"


def test_tts_failure_does_not_discard_text():
    controller = ConversationController(
        FakeRecorder(), FakeTranscriber(), FakeProvider(), FakeSpeaker(fail=True)
    )
    controller.start_recording()
    result = controller.finish_turn()
    assert result.assistant_text == "你好，有什么可以帮你？"


def test_failed_transcription_does_not_add_history():
    class BrokenTranscriber:
        def transcribe(self, path):
            raise TranscriptionError("bad audio")

    controller = ConversationController(
        FakeRecorder(), BrokenTranscriber(), FakeProvider(), FakeSpeaker()
    )
    controller.start_recording()
    try:
        controller.finish_turn()
    except TranscriptionError:
        pass
    assert controller.history == []
```

- [ ] **Step 2: Run and verify failure**

```bash
python -m pytest tests/test_controller.py -v
```

Expected: FAIL because controller is missing.

- [ ] **Step 3: Implement the controller**

Create `src/open_voice_box/controller.py`:

```python
from pathlib import Path

from open_voice_box.errors import SpeechError
from open_voice_box.models import Message, TurnResult


class ConversationController:
    def __init__(self, recorder, transcriber, provider, speaker):
        self.recorder = recorder
        self.transcriber = transcriber
        self.provider = provider
        self.speaker = speaker
        self.history: list[Message] = []

    def start_recording(self) -> None:
        self.recorder.start()

    def finish_turn(self) -> TurnResult:
        audio_path: Path = self.recorder.stop()
        try:
            transcription = self.transcriber.transcribe(audio_path)
            user_message = Message("user", transcription.text)
            request_history = [*self.history, user_message]
            assistant_text = self.provider.generate(request_history)
            assistant_message = Message("assistant", assistant_text)
            self.history.extend([user_message, assistant_message])
            try:
                self.speaker.speak(assistant_text)
            except SpeechError:
                # Text response remains usable even if audio output fails.
                pass
            return TurnResult(
                user_text=transcription.text,
                assistant_text=assistant_text,
                language=transcription.language,
            )
        finally:
            try:
                audio_path.unlink(missing_ok=True)
            except OSError:
                pass
```

- [ ] **Step 4: Run controller and full unit suite**

```bash
python -m pytest tests/test_controller.py -v
python -m pytest -q
```

Expected: controller tests PASS and full suite PASS.

- [ ] **Step 5: Commit**

```bash
git add src/open_voice_box/controller.py tests/test_controller.py
git commit -m "feat: orchestrate voice conversation turns"
```

---

### Task 7: Responsive Tkinter UI and application wiring

**Files:**
- Create: `src/open_voice_box/ui/__init__.py`
- Create: `src/open_voice_box/ui/main_window.py`
- Create: `src/open_voice_box/app.py`
- Create: `src/open_voice_box/__main__.py`
- Test: `tests/test_app.py`

**Interfaces:**
- UI receives a ready `ConversationController`.
- UI state strings: `Idle`, `Listening`, `Transcribing / Thinking`, `Speaking / Done`, `Error`.
- `finish_turn()` runs in a background thread; all Tk updates are marshalled through `root.after(...)`.

- [ ] **Step 1: Write a failing dependency-wiring smoke test**

Create `tests/test_app.py`:

```python
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
```

- [ ] **Step 2: Run and verify failure**

```bash
python -m pytest tests/test_app.py -v
```

Expected: FAIL because app module is missing.

- [ ] **Step 3: Implement application dependency wiring**

Create `src/open_voice_box/app.py`:

```python
import tkinter as tk

from open_voice_box.audio.recorder import PushToTalkRecorder
from open_voice_box.config import AppConfig
from open_voice_box.controller import ConversationController
from open_voice_box.llm.router import build_provider
from open_voice_box.stt.whisper import WhisperTranscriber
from open_voice_box.tts.macos import MacSpeaker
from open_voice_box.ui.main_window import MainWindow


def build_controller(config: AppConfig) -> ConversationController:
    return ConversationController(
        recorder=PushToTalkRecorder(),
        transcriber=WhisperTranscriber(config.stt_model),
        provider=build_provider(config),
        speaker=MacSpeaker(config.tts_voice),
    )


def main() -> None:
    config = AppConfig.from_env()
    controller = build_controller(config)
    root = tk.Tk()
    MainWindow(root, controller, provider_name=config.provider)
    root.mainloop()


if __name__ == "__main__":
    main()
```

Create `src/open_voice_box/__main__.py`:

```python
from open_voice_box.app import main

main()
```

Create empty `src/open_voice_box/ui/__init__.py`.

- [ ] **Step 4: Implement the Tkinter window with background turn processing**

Create `src/open_voice_box/ui/main_window.py`:

```python
import threading
import tkinter as tk
from tkinter import ttk

from open_voice_box.errors import OpenVoiceBoxError


class MainWindow:
    def __init__(self, root: tk.Tk, controller, provider_name: str):
        self.root = root
        self.controller = controller
        self.recording = False

        root.title("Open Voice Box")
        root.geometry("680x520")
        root.minsize(560, 420)

        container = ttk.Frame(root, padding=20)
        container.pack(fill="both", expand=True)

        ttk.Label(container, text="Open Voice Box", font=("TkDefaultFont", 22, "bold")).pack(anchor="w")
        ttk.Label(container, text=f"Provider: {provider_name}").pack(anchor="w", pady=(4, 16))

        self.status = tk.StringVar(value="Idle")
        ttk.Label(container, textvariable=self.status).pack(anchor="w", pady=(0, 12))

        self.transcript = tk.Text(container, wrap="word", height=16, state="disabled")
        self.transcript.pack(fill="both", expand=True)

        self.button = ttk.Button(container, text="Speak", command=self.toggle_recording)
        self.button.pack(fill="x", pady=(16, 0))

    def _append(self, speaker: str, text: str) -> None:
        self.transcript.configure(state="normal")
        self.transcript.insert("end", f"{speaker}: {text}\n\n")
        self.transcript.see("end")
        self.transcript.configure(state="disabled")

    def toggle_recording(self) -> None:
        if not self.recording:
            try:
                self.controller.start_recording()
            except OpenVoiceBoxError as exc:
                self.status.set(f"Error: {exc}")
                return
            self.recording = True
            self.status.set("Listening")
            self.button.configure(text="Stop")
            return

        self.recording = False
        self.button.configure(text="Speak", state="disabled")
        self.status.set("Transcribing / Thinking")
        threading.Thread(target=self._finish_turn_worker, daemon=True).start()

    def _finish_turn_worker(self) -> None:
        try:
            result = self.controller.finish_turn()
        except OpenVoiceBoxError as exc:
            self.root.after(0, self._show_error, str(exc))
            return
        except Exception:
            self.root.after(0, self._show_error, "Unexpected error. Please try again.")
            return
        self.root.after(0, self._show_result, result)

    def _show_result(self, result) -> None:
        self._append("You", result.user_text)
        self._append("Voice Box", result.assistant_text)
        self.status.set("Done")
        self.button.configure(state="normal")

    def _show_error(self, message: str) -> None:
        self.status.set(f"Error: {message}")
        self.button.configure(state="normal")
```

- [ ] **Step 5: Run smoke test and full test suite**

```bash
python -m pytest tests/test_app.py -v
python -m pytest -q
```

Expected: PASS.

- [ ] **Step 6: Manual UI smoke test with Ollama unavailable**

Run:

```bash
python -m open_voice_box
```

Expected:
- Window opens without freezing.
- `Speak` changes to `Stop` after microphone start.
- After `Stop`, button disables during processing.
- If Ollama is not running, a readable Ollama error appears and the app remains open.

- [ ] **Step 7: Commit**

```bash
git add src/open_voice_box/ui src/open_voice_box/app.py src/open_voice_box/__main__.py tests/test_app.py
git commit -m "feat: add desktop voice chat interface"
```

---

### Task 8: Open-source documentation, CI, issue templates, and V0.1 release gate

**Files:**
- Create: `README.md`
- Create: `README_CN.md`
- Create: `LICENSE`
- Create: `CONTRIBUTING.md`
- Create: `SECURITY.md`
- Create: `CHANGELOG.md`
- Create: `.github/workflows/ci.yml`
- Create: `.github/ISSUE_TEMPLATE/bug_report.yml`
- Create: `.github/ISSUE_TEMPLATE/feature_request.yml`

**Interfaces:**
- README setup must produce a working local flow using `ollama pull qwen3:4b-instruct` and `python -m open_voice_box`.
- Cloud instructions must identify OpenAI as optional and require the user's own API key.

- [ ] **Step 1: Add English README with exact setup and troubleshooting**

`README.md` must contain these sections and commands:

```markdown
# Open Voice Box

A local-first bilingual voice AI companion for macOS. Press a button, speak in Chinese or English, and hear the AI answer aloud.

## Why Open Voice Box?

- Local-first: Ollama is the default; no paid API key is required.
- Bilingual: local speech recognition auto-detects Chinese and English.
- Optional cloud mode: switch to OpenAI through environment configuration.
- Extensible: the provider, STT, recorder, and TTS layers are isolated for future hardware work.

## V0.1

V0.1 is macOS-first and uses push-to-talk. Wake words, persistent memory, Raspberry Pi, ESP32, camera, and animated faces are intentionally deferred.

## Quick start

### 1. Install prerequisites

Install Python 3.11 or newer and Ollama.

### 2. Pull the default local model

```bash
ollama pull qwen3:4b-instruct
```

### 3. Clone and install

```bash
git clone https://github.com/jonasnick629182-blip/open-voice-box.git
cd open-voice-box
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -e .
```

### 4. Run

```bash
python -m open_voice_box
```

On the first speech transcription, the Whisper model may need to download once.

## Optional OpenAI mode

```bash
cp .env.example .env
```

Set:

```dotenv
OVB_PROVIDER=openai
OPENAI_API_KEY=your_key_here
OVB_OPENAI_MODEL=gpt-5-mini
```

Never commit `.env`.

## Configuration

| Variable | Default | Purpose |
| --- | --- | --- |
| `OVB_PROVIDER` | `ollama` | `ollama` or `openai` |
| `OVB_OLLAMA_URL` | `http://localhost:11434` | Local Ollama URL |
| `OVB_OLLAMA_MODEL` | `qwen3:4b-instruct` | Local model |
| `OVB_OPENAI_MODEL` | `gpt-5-mini` | Optional cloud model |
| `OVB_STT_MODEL` | `small` | faster-whisper model |
| `OVB_TTS_VOICE` | empty | Optional macOS `say` voice |

## Troubleshooting

### Microphone permission

If recording fails, open macOS **System Settings → Privacy & Security → Microphone** and allow microphone access for the terminal/Python application you use to run Open Voice Box.

### Ollama is not reachable

Start Ollama, then verify the model exists:

```bash
ollama list
ollama pull qwen3:4b-instruct
```

### Speech model first-run download

The local speech model is downloaded on first use. Retry with a working internet connection, then subsequent use is local.

## Tests

```bash
python -m pip install -e '.[dev]'
python -m pytest -q
```

## Roadmap

- Wake word
- Better multilingual/local TTS
- Persistent opt-in memory
- Linux / Raspberry Pi validation
- ESP32 controls
- Screen / animated face
- Skills and home automation

## Contributing

See `CONTRIBUTING.md`.

## License

MIT
```

- [ ] **Step 2: Add Chinese README covering the same commands and constraints**

Create `README_CN.md` with a faithful Chinese version, preserving command names, environment variable names, local-first positioning, troubleshooting steps, and V0.1 exclusions. Do not add features that are absent from the English README.

- [ ] **Step 3: Add MIT license and contributor/security docs**

Create `LICENSE` using the standard MIT License with:

```text
Copyright (c) 2026 jonasnick629182-blip
```

Create `CONTRIBUTING.md` with this workflow:

```markdown
# Contributing

Thanks for helping improve Open Voice Box.

1. Open an issue before large changes.
2. Fork the repository and create a focused branch.
3. Keep each module responsible for one capability.
4. Add or update tests for behavior changes.
5. Run `python -m pytest -q` before opening a pull request.
6. Never commit API keys, `.env`, recordings, or personal data.

For V0.1, avoid adding wake words, persistence, hardware integrations, analytics, or unrelated UI frameworks unless the V0.1 design is explicitly revised first.
```

Create `SECURITY.md`:

```markdown
# Security Policy

Please do not publish API keys, credentials, private recordings, or personal data in issues.

For security-sensitive reports, contact the maintainer privately through the contact method listed on the maintainer's GitHub profile. Include a minimal reproduction and avoid attaching real secrets.

Open Voice Box stores V0.1 conversation history only in application memory. Temporary recordings are deleted after each turn on a best-effort basis.
```

Create `CHANGELOG.md`:

```markdown
# Changelog

All notable changes to this project will be documented here.

## [0.1.0] - 2026-08-15

### Added

- Push-to-talk macOS desktop interface.
- Local Chinese/English transcription with faster-whisper.
- Local Ollama chat with `qwen3:4b-instruct` as the default model.
- Optional OpenAI Responses API provider.
- Local macOS text-to-speech.
- Memory-only multi-turn conversation context.
- Recoverable user-facing errors and automated unit tests.
```

- [ ] **Step 4: Add CI that installs the package and runs unit tests**

Create `.github/workflows/ci.yml`:

```yaml
name: CI

on:
  push:
    branches: [main]
  pull_request:

jobs:
  test:
    runs-on: macos-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.11"
      - run: python -m pip install --upgrade pip
      - run: python -m pip install -e '.[dev]'
      - run: python -m pytest -q
```

- [ ] **Step 5: Add issue templates**

Create `.github/ISSUE_TEMPLATE/bug_report.yml`:

```yaml
name: Bug report
description: Report a reproducible Open Voice Box problem
title: "[Bug]: "
labels: [bug]
body:
  - type: textarea
    attributes:
      label: What happened?
    validations:
      required: true
  - type: input
    attributes:
      label: macOS / OS version
    validations:
      required: true
  - type: input
    attributes:
      label: Python version
    validations:
      required: true
  - type: dropdown
    attributes:
      label: Provider
      options: [Ollama, OpenAI]
    validations:
      required: true
  - type: textarea
    attributes:
      label: Reproduction steps
    validations:
      required: true
  - type: textarea
    attributes:
      label: Logs
      description: Remove API keys, personal data, and private transcripts before posting.
```

Create `.github/ISSUE_TEMPLATE/feature_request.yml`:

```yaml
name: Feature request
description: Suggest a focused improvement
title: "[Feature]: "
labels: [enhancement]
body:
  - type: textarea
    attributes:
      label: Problem
      description: What user problem should this solve?
    validations:
      required: true
  - type: textarea
    attributes:
      label: Proposed behavior
    validations:
      required: true
  - type: textarea
    attributes:
      label: Why it belongs in Open Voice Box
    validations:
      required: true
```

- [ ] **Step 6: Verify packaging, tests, documentation files, and secret hygiene**

Run:

```bash
python -m pytest -q
python -m pip install -e .
python -m open_voice_box
```

Close the GUI after confirming it launches.

Then run:

```bash
python - <<'PY'
from pathlib import Path
required = [
    "README.md", "README_CN.md", "LICENSE", "CONTRIBUTING.md",
    "SECURITY.md", "CHANGELOG.md", ".env.example",
    ".github/workflows/ci.yml",
]
missing = [path for path in required if not Path(path).exists()]
assert not missing, missing
print("documentation gate: PASS")
PY

git grep -nE 'sk-[A-Za-z0-9_-]{12,}|OPENAI_API_KEY=.+[^= ]' -- ':!docs/superpowers/**' || true
```

Expected:
- Tests PASS.
- App launches.
- Documentation gate prints `PASS`.
- Secret grep does not reveal a real key.

- [ ] **Step 7: Perform the real local V0.1 acceptance test on the target Mac**

Prerequisite:

```bash
ollama pull qwen3:4b-instruct
```

Run:

```bash
OVB_PROVIDER=ollama python -m open_voice_box
```

Manually verify all of these, recording the result in the PR/release notes rather than inventing results:

1. Press `Speak`, say a Chinese sentence, press `Stop`; Chinese transcript appears, Ollama responds, and audio plays.
2. Press `Speak`, say an English sentence, press `Stop`; English transcript appears, Ollama responds, and audio plays.
3. Quit Ollama and retry; the app shows a readable Ollama error and stays open.
4. Restart Ollama; a new turn succeeds without restarting the app if the provider client remains usable, otherwise restart the app and document that limitation.
5. Set `OVB_OLLAMA_MODEL` to a missing model; error message includes the exact `ollama pull <model>` command.
6. Deny microphone permission temporarily if practical; app shows the microphone guidance instead of crashing.
7. Confirm no `.wav` file from the completed turns remains in the repository working tree.

Optional cloud acceptance, only if the maintainer has their own API credit:

```bash
OVB_PROVIDER=openai OPENAI_API_KEY='...' python -m open_voice_box
```

Verify one turn and never store the key in shell history if that is a concern; `.env` is the recommended local alternative and is ignored by Git.

- [ ] **Step 8: Commit documentation and release-ready repository metadata**

```bash
git add README.md README_CN.md LICENSE CONTRIBUTING.md SECURITY.md CHANGELOG.md .github
git commit -m "docs: prepare open voice box v0.1"
```

---

## Final Verification Before Calling V0.1 Complete

Run this exact sequence from a clean checkout on the target Mac:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -e '.[dev]'
python -m pytest -q
ollama pull qwen3:4b-instruct
OVB_PROVIDER=ollama python -m open_voice_box
```

Do not claim V0.1 is complete unless:

- Automated tests pass.
- The GUI opens and remains responsive while transcription/generation runs.
- A Chinese voice turn succeeds end-to-end locally.
- An English voice turn succeeds end-to-end locally.
- Ollama mode works with no paid API key.
- Text remains visible if TTS playback fails.
- Missing Ollama/model/microphone configuration produces a recoverable readable error.
- No secret or temporary recording is committed.

## Implementation Notes / Verified External Interfaces

- Ollama chat uses `POST /api/chat`, with `stream: false`; thinking-capable models such as Qwen 3 accept `think: false` so V0.1 can avoid returning a reasoning trace and reduce voice-chat latency.
- `qwen3:4b-instruct` exists in the Ollama model library and is a practical small multilingual model candidate for a 16 GB Apple Silicon machine; final latency must still be measured on the target Mac rather than assumed.
- faster-whisper accepts a file path, can auto-detect language when `language=None`, and exposes detected language in transcription info; its VAD filter can be enabled during transcription.
- The official OpenAI Python SDK supports the Responses API through `client.responses.create(...)`, and `response.output_text` is the convenience property used for text output.
- python-sounddevice supports macOS and exposes callback-based `InputStream`, which is more appropriate than fixed-duration convenience recording for push-to-talk.

## Self-Review Result

- **Spec coverage:** All V0.1 requirements are mapped: push-to-talk, bilingual STT, Ollama default, optional OpenAI, TTS, visible transcript, provider config, recoverable errors, memory-only history, tests, docs, and open-source hygiene.
- **Scope check:** Wake word, persistent memory, camera, Raspberry Pi/ESP32, animated face, home automation, accounts, cloud sync, payments, analytics, and telemetry remain excluded.
- **Placeholder scan:** No TBD/TODO implementation placeholders are present. Manual acceptance explicitly requires recording real results instead of assuming success.
- **Type/interface consistency:** `AppConfig`, `Message`, `TurnResult`, `LLMProvider.generate`, `WhisperTranscriber.transcribe`, `PushToTalkRecorder.start/stop`, `MacSpeaker.speak`, and `ConversationController.start_recording/finish_turn` use consistent names across tasks.
