from pathlib import Path
import tempfile
import threading

import numpy as np
import soundfile as sf

from open_voice_box.errors import AudioInputError

try:
    import sounddevice as sd
except ImportError:
    class _SoundDeviceShim:
        @staticmethod
        def InputStream(*args, **kwargs):
            raise RuntimeError(
                "sounddevice is not installed. Reinstall project dependencies."
            )

    sd = _SoundDeviceShim()


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
