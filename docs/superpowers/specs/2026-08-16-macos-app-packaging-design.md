# Open Voice Box macOS App Packaging Design

Date: 2026-08-16
Issue: #4 — Package Open Voice Box as a standalone macOS app
Target release: v0.2.0

## 1. Goal

Package Open Voice Box as a normal macOS `.app` so an Apple Silicon Mac user can launch it by double-clicking instead of creating a Python virtual environment and running a terminal command.

The first packaging milestone is a reproducible development build for Apple Silicon macOS. It is not an App Store or notarized production distribution.

## 2. Scope

### In scope

- Build an Apple Silicon macOS `.app` using PyInstaller.
- Use PyInstaller `--windowed` / onedir-style application bundling rather than a one-file bundle.
- Bundle Python, Open Voice Box source code, and practical Python runtime dependencies.
- Keep Ollama as an external prerequisite.
- Keep the Whisper speech model as a first-run/runtime download rather than embedding it in the application bundle.
- Preserve the existing provider/model selector and local-first behavior.
- Add application metadata, including app name, version, bundle identifier, and microphone usage description.
- Add an application icon if a suitable repository-owned icon asset is available; otherwise use a minimal placeholder that can be replaced without changing the packaging architecture.
- Add reproducible local build instructions.
- Extend GitHub Actions CI with a macOS packaging/build smoke test.
- Verify that the packaged app keeps the existing understandable error states for missing Ollama, missing model, microphone problems, and speech-model loading failures.

### Out of scope

- Mac App Store distribution.
- Apple Developer ID signing, notarization, or paid Apple Developer requirements.
- DMG/PKG distribution packaging.
- Intel/x86_64 macOS support.
- Windows packaging.
- Raspberry Pi packaging.
- Bundling Ollama into the app.
- Bundling the Whisper model into the app.

## 3. Chosen approach

Use **PyInstaller with a checked-in spec file** to create `Open Voice Box.app` as a windowed onedir-style bundle.

This is preferred over py2app or Briefcase because the current project already has a simple `pyproject.toml` Python layout, a single Tkinter application entry point, and working runtime dependencies. PyInstaller adds the least project-wide machinery while still supporting macOS application bundles and `Info.plist` customization.

The build should remain explicit and reproducible through one documented command or one small repository build script that invokes the spec file.

## 4. Application architecture after packaging

The packaged app keeps the existing runtime architecture:

1. Tkinter starts the desktop window.
2. `AppConfig.from_env()` loads configuration.
3. `PushToTalkRecorder` records microphone input.
4. `WhisperTranscriber` lazy-loads the configured faster-whisper model.
5. `build_provider()` routes to Ollama or the optional OpenAI-compatible provider.
6. `MacSpeaker` produces the spoken response.

Packaging must not introduce a second application codepath. The normal Python entry point and the packaged app should call the same `open_voice_box.app:main` flow.

## 5. External prerequisites and first-run behavior

### Ollama

Ollama remains external. The app should connect to the existing default endpoint at `http://localhost:11434` unless configured otherwise.

If Ollama is unavailable, the UI should preserve or improve the current recoverable message rather than crashing.

If the configured Ollama model is missing, the UI should tell the user which `ollama pull <model>` command is needed.

### Whisper model

The faster-whisper model remains runtime-managed. The app does not embed the model files.

On first speech use, the existing lazy-loading behavior may download the configured model. If that operation fails, the user should see a clear retry/network message rather than a Python traceback.

### OpenAI provider

The optional OpenAI-compatible provider remains supported through existing environment/config behavior. No API key is embedded in the app bundle.

## 6. macOS metadata and permissions

The generated `.app` must include:

- Display name: `Open Voice Box`
- Version: `0.2.0`
- Bundle identifier: `io.github.jonasnick629182-blip.openvoicebox`
- `NSMicrophoneUsageDescription`: a short user-facing explanation that Open Voice Box needs microphone access to record push-to-talk voice input.

The packaged app must be able to trigger or participate in macOS microphone permission handling as a normal application. Manual acceptance testing should confirm the app appears correctly in System Settings > Privacy & Security > Microphone after permission is requested.

Because this release is unsigned/unnotarized, documentation must explicitly explain that macOS Gatekeeper may require the user to use Finder > Open (or the equivalent contextual-open flow) on first launch.

## 7. Packaging files

The implementation should add focused packaging artifacts, expected to include:

- A PyInstaller `.spec` file dedicated to Open Voice Box.
- A small build command/script if it materially improves reproducibility.
- An app icon asset if available.
- Documentation covering prerequisites, local build, launch, and known unsigned-app behavior.
- CI changes for a packaging smoke build.

Packaging-specific logic should not be scattered through the application source unless runtime behavior truly needs it.

## 8. Hidden imports and bundled resources

PyInstaller analysis must be verified against the current dependency graph, especially:

- Tkinter/Tcl/Tk runtime pieces.
- `sounddevice` and its native dependencies.
- `soundfile` / libsndfile-related runtime files.
- faster-whisper / CTranslate2 / tokenizers / model-loading modules.
- OpenAI/httpx dependencies.

The implementation should add hidden imports or resource collection only when a reproducible build/test demonstrates they are required. Avoid broad "collect everything" rules unless necessary because they increase bundle size and make failures harder to diagnose.

## 9. Error handling expectations

The packaged app must not silently fail or open only a terminal traceback for expected environment problems.

The existing UI-level recoverable behavior should cover:

- Ollama unavailable.
- Ollama model missing.
- Microphone unavailable or denied.
- No audio captured.
- Speech model load/download failure.
- Speech transcription failure.

If packaging changes how any of these exceptions surface, that regression must be fixed before release.

## 10. Testing strategy

### Automated tests

Existing unit tests must continue passing.

CI should add a macOS packaging job or step that:

1. Installs project and packaging dependencies.
2. Runs the PyInstaller build.
3. Asserts that `dist/Open Voice Box.app` (or the final agreed bundle path) exists.
4. Performs a lightweight structural smoke check on the bundle without requiring microphone interaction or a running Ollama service.

CI does not need to perform an interactive GUI launch or voice round trip.

### Manual acceptance testing on Apple Silicon Mac

Before closing Issue #4 and publishing v0.2.0, manually verify:

1. A fresh packaged build opens by double-clicking the `.app`.
2. The window appears without a terminal window.
3. The app can request/use microphone permission.
4. Chinese push-to-talk completes: record → transcribe → local LLM → audible reply.
5. English push-to-talk completes: record → transcribe → local LLM → audible reply.
6. Missing Ollama produces a clear recoverable message.
7. Missing configured Ollama model produces a clear command/action hint.
8. Whisper first-run loading failure is understandable and recoverable.
9. Temporary WAV cleanup behavior remains correct.

## 11. Release workflow

Implementation should follow a normal maintenance cycle:

1. Work on a dedicated feature branch.
2. Add tests/packaging checks before or alongside implementation changes.
3. Open a PR referencing Issue #4.
4. Require CI to pass.
5. Merge to `main`.
6. Close Issue #4 when acceptance criteria are met.
7. Publish `v0.2.0` with release notes that clearly state it is an unsigned Apple Silicon development `.app` and list required external prerequisites.

## 12. Success criteria

Issue #4 is complete when all of the following are true:

- An Apple Silicon Mac can open the generated `.app` without a Python virtual environment.
- The app launches as a GUI application without a terminal window.
- Ollama remains external and its absence is handled clearly.
- The Whisper model remains runtime-downloaded and model-load failures are handled clearly.
- Microphone permission works as a normal macOS app flow.
- Chinese and English push-to-talk still work end to end on a real Mac.
- Packaging is reproducible from repository instructions.
- CI can build and structurally validate the `.app` bundle.
- Existing tests remain green.

## 13. Non-goals for v0.2.0

v0.2.0 is a developer-distribution milestone, not a polished consumer installer. We deliberately prefer a smaller, testable packaging step over adding signing, notarization, DMG creation, Intel support, or embedded model assets before the core `.app` path has been proven reliable.
