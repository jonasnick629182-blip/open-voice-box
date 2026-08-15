# Open Voice Box

A local-first bilingual voice AI companion for macOS. Press a button, speak in Chinese or English, and hear the AI answer aloud.

## Why Open Voice Box?

- **Local-first:** Ollama is the default; no paid API key is required.
- **Bilingual:** local speech recognition auto-detects Chinese and English.
- **Optional cloud mode:** switch to OpenAI through environment configuration.
- **Extensible:** the provider, STT, recorder, and TTS layers are isolated for future hardware work.

## V0.1

V0.1 is macOS-first and uses push-to-talk. Wake words, persistent memory, Raspberry Pi, ESP32, camera, and animated faces are intentionally deferred.

## Quick start

### 1. Install prerequisites

Install Python 3.11 or newer and Ollama.

### 2. Pull the default local model

```bash
ollama pull qwen3:4b-instruct
```

### 3. Clone and install

```bash
git clone https://github.com/jonasnick629182-blip/open-voice-box.git
cd open-voice-box
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -e .
```

### 4. Run

```bash
python -m open_voice_box
```

On the first speech transcription, the Whisper model may need to download once.

## Optional OpenAI mode

```bash
cp .env.example .env
```

Set:

```dotenv
OVB_PROVIDER=openai
OPENAI_API_KEY=your_key_here
OVB_OPENAI_MODEL=gpt-5-mini
```

Never commit `.env`.

## Configuration

| Variable | Default | Purpose |
| --- | --- | --- |
| `OVB_PROVIDER` | `ollama` | `ollama` or `openai` |
| `OVB_OLLAMA_URL` | `http://localhost:11434` | Local Ollama URL |
| `OVB_OLLAMA_MODEL` | `qwen3:4b-instruct` | Local model |
| `OVB_OPENAI_MODEL` | `gpt-5-mini` | Optional cloud model |
| `OVB_STT_MODEL` | `small` | faster-whisper model |
| `OVB_TTS_VOICE` | empty | Optional macOS `say` voice |

## Troubleshooting

### Microphone permission

If recording fails, open macOS **System Settings → Privacy & Security → Microphone** and allow microphone access for the terminal/Python application you use to run Open Voice Box.

### Ollama is not reachable

Start Ollama, then verify the model exists:

```bash
ollama list
ollama pull qwen3:4b-instruct
```

### Speech model first-run download

The local speech model is downloaded on first use. Retry with a working internet connection, then subsequent use is local.

## Tests

```bash
python -m pip install -e '.[dev]'
python -m pytest -q
```

## Roadmap

- Wake word
- Better multilingual/local TTS
- Persistent opt-in memory
- Linux / Raspberry Pi validation
- ESP32 controls
- Screen / animated face
- Skills and home automation

## Contributing

See `CONTRIBUTING.md`.

## License

MIT
