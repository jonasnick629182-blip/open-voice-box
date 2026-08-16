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
