# Open Voice Box V0.1 Design

## 1. Goal

Build the first usable version of Open Voice Box: a small bilingual desktop voice companion that can run primarily with free local models and optionally switch to cloud APIs.

V0.1 success criterion:

> A user on macOS can launch the app, press one button, speak in Chinese or English, see the transcription, receive an AI response, and hear that response spoken aloud.

The first release should optimize for reliability, clarity, and ease of installation rather than feature count.

## 2. Scope

### Included in V0.1

- macOS-first desktop experience.
- One-button push-to-talk interaction.
- Chinese and English speech input.
- Speech-to-text using a local Whisper-family model.
- Local LLM mode through Ollama.
- Optional cloud LLM provider support through a provider abstraction.
- Text-to-speech playback.
- Visible conversation transcript in a minimal desktop UI.
- Configurable model/provider settings.
- Clear error messages for missing microphone permission, unavailable Ollama, missing model, and invalid cloud credentials.
- Basic automated tests for provider routing and core application logic.

### Explicitly excluded from V0.1

- Wake-word detection.
- Always-on listening.
- Long-term memory.
- Camera/vision.
- Raspberry Pi and ESP32 hardware integration.
- Animated face or screen UI.
- Home automation.
- User accounts, cloud sync, payments, analytics, or telemetry.

These are future extensions and must not complicate the first release.

## 3. Primary User Flow

1. User launches the application.
2. App performs a lightweight startup check:
   - microphone access available,
   - local configuration readable,
   - selected LLM provider reachable.
3. User presses `Speak`.
4. App records microphone audio until the user presses `Stop` or a simple silence/end condition is reached.
5. Audio is transcribed to text.
6. Transcribed text is shown in the UI.
7. The LLM router sends the text to the selected provider:
   - Local: Ollama,
   - Cloud: configured provider.
8. The response text appears in the UI.
9. Text-to-speech reads the answer aloud.
10. The app returns to an idle state, ready for the next turn.

## 4. Architecture

Use a small modular Python architecture so each capability can be replaced independently.

```text
Desktop UI
   |
   v
Conversation Controller
   |
   +--> Recorder
   |
   +--> Speech-to-Text
   |
   +--> LLM Router
   |      +--> Ollama Provider
   |      +--> Cloud Provider(s)
   |
   +--> Text-to-Speech
   |
   +--> Config
```

The UI must not call external model APIs directly. All orchestration should go through the conversation controller. Provider-specific behavior stays behind interfaces so future models can be added without rewriting the application flow.

## 5. Components

### 5.1 Desktop UI

Recommended stack: Python with Tkinter or CustomTkinter.

Responsibilities:

- `Speak` / `Stop` controls.
- Current status: Idle, Listening, Transcribing, Thinking, Speaking, Error.
- Display latest user transcription and assistant answer.
- Provider/model selector.
- Small settings panel for local/cloud configuration.

The interface should remain intentionally minimal in V0.1.

### 5.2 Recorder

Responsibilities:

- Open the default microphone.
- Record mono speech audio at a format accepted by the speech-to-text layer.
- Start and stop cleanly.
- Return a temporary audio file or in-memory audio buffer.

The recorder must fail clearly when microphone permission is denied or no input device is available.

### 5.3 Speech-to-Text

Recommended implementation: `faster-whisper` or an equivalent local Whisper implementation.

Responsibilities:

- Accept recorded audio.
- Auto-detect Chinese or English.
- Return normalized transcript text plus detected language when available.

V0.1 does not need word-level timestamps or subtitles.

### 5.4 LLM Router

Expose a simple provider-neutral interface such as:

```text
generate(messages, settings) -> text
```

The router selects the active provider from configuration.

#### Ollama provider

- Default local mode.
- Connect to the local Ollama HTTP service.
- Use a model suitable for a 16 GB Apple Silicon Mac.
- Default model should be modest in size, approximately 3B-8B class, with the exact recommendation documented in README after implementation testing.

#### Cloud provider

- Optional.
- Must be implemented through the same provider interface.
- Secrets are read from environment variables or a local config file that is ignored by Git.
- No API key is ever committed to the repository.

The first cloud implementation should favor simplicity and compatibility; additional providers can be added later.

### 5.5 Text-to-Speech

V0.1 should prefer a low-friction local solution.

Responsibilities:

- Speak Chinese and English responses.
- Avoid requiring a paid service.
- Provide a clean interface so higher-quality TTS can be added later.

On macOS, the initial implementation may use the system speech engine if it gives acceptable bilingual output. A cross-platform fallback can be added after the first working release.

### 5.6 Configuration

Configuration should include:

- active provider,
- local Ollama endpoint,
- local model name,
- cloud provider name,
- cloud model name,
- preferred TTS voice when supported,
- speech recognition model size.

Use safe defaults. Sensitive keys must come from environment variables or an ignored local file.

## 6. Data Flow

For each conversation turn:

```text
Microphone audio
  -> Recorder
  -> temporary audio/buffer
  -> Speech-to-Text
  -> user text
  -> Conversation Controller
  -> LLM Router
  -> selected LLM provider
  -> assistant text
  -> UI transcript
  -> Text-to-Speech
  -> speaker output
```

V0.1 conversation context can remain in memory for the current session only. Persistent memory is intentionally deferred.

## 7. Error Handling

The application should translate technical failures into user-readable messages.

Required cases:

- Microphone permission denied: explain how to enable microphone access on macOS.
- No microphone found: show a clear device error.
- Ollama not installed or not running: explain that local mode requires Ollama and provide the next action.
- Selected Ollama model missing: show the exact model pull command.
- Speech model download/initialization failure: show a retryable error.
- Cloud key missing: disable cloud generation and explain which environment variable is required.
- Cloud request timeout/rate limit: keep the app running and allow another attempt.
- TTS failure: still display the text answer even when speech playback fails.
- Empty/unclear transcription: do not send an empty request to the LLM.

A failure in one stage must not crash the whole application where recovery is possible.

## 8. Performance Expectations

For the target development machine (Apple Silicon MacBook Air, 16 GB RAM):

- UI should remain responsive during transcription and generation.
- Heavy work should run outside the UI thread.
- Local model choice should prioritize response latency over maximum reasoning quality.
- First-run model downloads may be slow, but subsequent turns should not redownload models.

No strict latency SLA is required for V0.1; perceived responsiveness and stability matter more.

## 9. Testing Strategy

### Unit tests

Test the logic that does not require real microphone/audio/model access:

- provider routing,
- configuration parsing,
- missing-key handling,
- empty transcript handling,
- controller state transitions,
- provider error normalization.

### Integration tests

Use mocks/fakes for:

- speech-to-text,
- Ollama responses,
- cloud provider responses,
- text-to-speech.

A basic end-to-end manual test should verify:

1. Chinese input -> Chinese or context-appropriate answer -> audible playback.
2. English input -> English or context-appropriate answer -> audible playback.
3. Local Ollama mode works with no paid API key.
4. Switching to the cloud provider works when valid credentials are supplied.
5. Missing Ollama/cloud configuration produces a useful error instead of a crash.

## 10. Repository Shape

Target structure after implementation planning:

```text
open-voice-box/
├── README.md
├── README_CN.md
├── LICENSE
├── CONTRIBUTING.md
├── SECURITY.md
├── CHANGELOG.md
├── pyproject.toml
├── .gitignore
├── .env.example
├── src/
│   └── open_voice_box/
│       ├── app.py
│       ├── controller.py
│       ├── config.py
│       ├── audio/
│       ├── stt/
│       ├── llm/
│       ├── tts/
│       └── ui/
├── tests/
├── docs/
└── .github/
    ├── ISSUE_TEMPLATE/
    └── workflows/
```

The exact file breakdown may be refined in the implementation plan, but module boundaries should remain consistent with this design.

## 11. Open-Source Positioning

The project should be presented as a real reusable OSS tool, not as a one-off demo.

Core message:

> Turn a Mac, Linux machine, or later a Raspberry Pi into a simple bilingual voice AI companion, with a free local-first path and optional cloud models.

V0.1 should make contribution easy through a clear README, MIT license, contribution guide, issue templates, and reproducible setup. Future releases can extend the same architecture toward wake words, persistent memory, hardware, and robot-style interfaces.

## 12. Release Gate for V0.1

V0.1 is ready only when all of the following are true:

- A fresh macOS user can follow the README and launch the app.
- Local Ollama mode works without any paid API key.
- Chinese and English speech can both be transcribed.
- The app can produce and audibly speak an answer.
- Provider switching works through configuration rather than code edits.
- Common configuration failures are recoverable and clearly explained.
- Core automated tests pass.
- No secrets are stored in the repository.

Anything beyond these criteria is deferred to a later release.
