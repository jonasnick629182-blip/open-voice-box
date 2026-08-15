import threading
import tkinter as tk
from tkinter import ttk

from open_voice_box.errors import OpenVoiceBoxError


class MainWindow:
    def __init__(self, root: tk.Tk, controller, provider_name: str):
        self.root = root
        self.controller = controller
        self.recording = False

        root.title("Open Voice Box")
        root.geometry("680x520")
        root.minsize(560, 420)

        container = ttk.Frame(root, padding=20)
        container.pack(fill="both", expand=True)

        ttk.Label(
            container,
            text="Open Voice Box",
            font=("TkDefaultFont", 22, "bold"),
        ).pack(anchor="w")
        ttk.Label(container, text=f"Provider: {provider_name}").pack(
            anchor="w", pady=(4, 16)
        )

        self.status = tk.StringVar(value="Idle")
        ttk.Label(container, textvariable=self.status).pack(anchor="w", pady=(0, 12))

        self.transcript = tk.Text(container, wrap="word", height=16, state="disabled")
        self.transcript.pack(fill="both", expand=True)

        self.button = ttk.Button(container, text="Speak", command=self.toggle_recording)
        self.button.pack(fill="x", pady=(16, 0))

    def _append(self, speaker: str, text: str) -> None:
        self.transcript.configure(state="normal")
        self.transcript.insert("end", f"{speaker}: {text}\n\n")
        self.transcript.see("end")
        self.transcript.configure(state="disabled")

    def toggle_recording(self) -> None:
        if not self.recording:
            try:
                self.controller.start_recording()
            except OpenVoiceBoxError as exc:
                self.status.set(f"Error: {exc}")
                return
            self.recording = True
            self.status.set("Listening")
            self.button.configure(text="Stop")
            return

        self.recording = False
        self.button.configure(text="Speak", state="disabled")
        self.status.set("Transcribing / Thinking")
        threading.Thread(target=self._finish_turn_worker, daemon=True).start()

    def _finish_turn_worker(self) -> None:
        try:
            result = self.controller.finish_turn()
        except OpenVoiceBoxError as exc:
            self.root.after(0, self._show_error, str(exc))
            return
        except Exception:
            self.root.after(0, self._show_error, "Unexpected error. Please try again.")
            return
        self.root.after(0, self._show_result, result)

    def _show_result(self, result) -> None:
        self._append("You", result.user_text)
        self._append("Voice Box", result.assistant_text)
        self.status.set("Done")
        self.button.configure(state="normal")

    def _show_error(self, message: str) -> None:
        self.status.set(f"Error: {message}")
        self.button.configure(state="normal")
