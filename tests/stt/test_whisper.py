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
