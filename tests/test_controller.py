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


def test_provider_can_be_switched_for_future_turns():
    first = FakeProvider()
    second = FakeProvider()
    controller = ConversationController(
        FakeRecorder(), FakeTranscriber(), first, FakeSpeaker()
    )
    controller.set_provider(second)
    controller.start_recording()
    controller.finish_turn()
    assert second.messages == [Message("user", "你好")]
    assert first.messages is None
