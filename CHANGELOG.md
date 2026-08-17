# Changelog

All notable changes to this project will be documented here.

## [0.2.0] - 2026-08-16

### Added

- Reproducible PyInstaller-based macOS `.app` packaging.
- macOS bundle metadata and microphone usage description.
- Deterministic build-time app icon generation.
- Structural `.app` verification and CI packaging smoke coverage.
- Documentation for unsigned Gatekeeper launch and Apple Silicon testing.

### Changed

- Project/package version updated to 0.2.0.
- Ollama remains external and faster-whisper models remain runtime-managed.

## [0.1.0] - 2026-08-15

### Added

- Push-to-talk macOS desktop interface.
- Local Chinese/English transcription with faster-whisper.
- Local Ollama chat with `qwen3:4b-instruct` as the default model.
- Optional OpenAI Responses API provider.
- Local macOS text-to-speech.
- Memory-only multi-turn conversation context.
- Recoverable user-facing errors and automated unit tests.
