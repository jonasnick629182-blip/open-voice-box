from dataclasses import dataclass
from pathlib import Path

from open_voice_box.errors import TranscriptionError

try:
    from faster_whisper import WhisperModel
except ImportError:
    WhisperModel = None


@dataclass(frozen=True)
class Transcription:
    text: str
    language: str | None


class WhisperTranscriber:
    def __init__(self, model_name: str = "small", model=None):
        try:
            if model is not None:
                self.model = model
            else:
                if WhisperModel is None:
                    raise ImportError("faster-whisper is not installed")
                self.model = WhisperModel(
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
            text = " ".join(
                segment.text.strip()
                for segment in segments
                if segment.text.strip()
            ).strip()
        except Exception as exc:
            raise TranscriptionError("Speech transcription failed. Please try again.") from exc
        if not text:
            raise TranscriptionError("I could not understand any speech. Please try again.")
        return Transcription(text=text, language=getattr(info, "language", None))
