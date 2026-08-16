from dataclasses import replace
import threading
import tkinter as tk
from tkinter import ttk

from open_voice_box.config import AppConfig
from open_voice_box.errors import OpenVoiceBoxError


def with_provider_settings(config: AppConfig, provider: str, model: str) -> AppConfig:
    provider = provider.strip().lower()
    model = model.strip()
    if provider not in {"ollama", "openai"}:
        raise ValueError("Provider must be 'ollama' or 'openai'.")
    if not model:
        raise ValueError("Model name cannot be empty.")
    if provider == "ollama":
        return replace(config, provider="ollama", ollama_model=model)
    return replace(config, provider="openai", openai_model=model)


class MainWindow:
    def __init__(self, root: tk.Tk, controller, config: AppConfig, provider_factory):
        self.root = root
        self.controller = controller
        self.config = config
        self.provider_factory = provider_factory
        self.recording = False

        root.title("Open Voice Box")
        root.geometry("680x580")
        root.minsize(560, 470)

        container = ttk.Frame(root, padding=20)
        container.pack(fill="both", expand=True)

        ttk.Label(
            container,
            text="Open Voice Box",
            font=("TkDefaultFont", 22, "bold"),
        ).pack(anchor="w")

        settings = ttk.LabelFrame(container, text="Model settings", padding=10)
        settings.pack(fill="x", pady=(10, 14))

        ttk.Label(settings, text="Provider").grid(row=0, column=0, sticky="w")
        self.provider_var = tk.StringVar(value=config.provider)
        provider_box = ttk.Combobox(
            settings,
            textvariable=self.provider_var,
            values=("ollama", "openai"),
            state="readonly",
            width=12,
        )
        provider_box.grid(row=0, column=1, sticky="ew", padx=(8, 12))
        provider_box.bind("<<ComboboxSelected>>", self._provider_selected)

        ttk.Label(settings, text="Model").grid(row=0, column=2, sticky="w")
        initial_model = (
            config.ollama_model if config.provider == "ollama" else config.openai_model
        )
        self.model_var = tk.StringVar(value=initial_model)
        ttk.Entry(settings, textvariable=self.model_var).grid(
            row=0, column=3, sticky="ew", padx=(8, 12)
        )
        ttk.Button(settings, text="Apply", command=self.apply_provider_settings).grid(
            row=0, column=4
        )
        settings.columnconfigure(3, weight=1)

        self.status = tk.StringVar(value="Idle")
        ttk.Label(container, textvariable=self.status).pack(anchor="w", pady=(0, 12))

        self.transcript = tk.Text(container, wrap="word", height=16, state="disabled")
        self.transcript.pack(fill="both", expand=True)

        self.button = ttk.Button(container, text="Speak", command=self.toggle_recording)
        self.button.pack(fill="x", pady=(16, 0))

    def _provider_selected(self, _event=None) -> None:
        if self.provider_var.get() == "ollama":
            self.model_var.set(self.config.ollama_model)
        else:
            self.model_var.set(self.config.openai_model)

    def apply_provider_settings(self) -> None:
        try:
            new_config = with_provider_settings(
                self.config, self.provider_var.get(), self.model_var.get()
            )
            provider = self.provider_factory(new_config)
        except (OpenVoiceBoxError, ValueError) as exc:
            self.status.set(f"Error: {exc}")
            return
        self.config = new_config
        self.controller.set_provider(provider)
        self.status.set(
            f"Ready: {new_config.provider} / "
            f"{new_config.ollama_model if new_config.provider == 'ollama' else new_config.openai_model}"
        )

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
