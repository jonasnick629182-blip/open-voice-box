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
        self.model_name = model_name
        self.model = model

    def _get_model(self):
        if self.model is not None:
            return self.model
        try:
            if WhisperModel is None:
                raise ImportError("faster-whisper is not installed")
            self.model = WhisperModel(
                self.model_name,
                device="cpu",
                compute_type="int8",
            )
            return self.model
        except Exception as exc:
            raise TranscriptionError(
                "Speech model could not be loaded. Check the network on first run and try again."
            ) from exc

    def transcribe(self, path: Path) -> Transcription:
        model = self._get_model()
        try:
            segments, info = model.transcribe(
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
            raise TranscriptionError(
                "I could not understand any speech. Check macOS System Settings > "
                "Privacy & Security > Microphone and make sure Terminal/Python has "
                "microphone access, then try again."
            )
        return Transcription(text=text, language=getattr(info, "language", None))
