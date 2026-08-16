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
