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
