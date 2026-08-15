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

    def set_provider(self, provider) -> None:
        self.provider = provider

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
