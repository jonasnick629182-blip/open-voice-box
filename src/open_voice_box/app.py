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
    MainWindow(root, controller, config=config, provider_factory=build_provider)
    root.mainloop()


if __name__ == "__main__":
    main()
