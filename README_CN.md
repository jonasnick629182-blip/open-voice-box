# Open Voice Box

一个本地优先的中英双语语音 AI 助手，V0.1 面向 macOS。按下按钮，用中文或英文说话，AI 会生成回答并通过系统语音朗读。

## 为什么做 Open Voice Box？

- **本地优先：** 默认使用 Ollama，不要求付费 API Key。
- **中英双语：** 本地语音识别自动判断中文或英文。
- **可选云端模式：** 可以通过环境变量切换到 OpenAI。
- **方便扩展：** LLM、语音识别、录音和语音播报互相隔离，后续可以继续接入硬件。

## V0.1 范围

V0.1 以 macOS 为第一支持平台，采用按键说话。唤醒词、长期记忆、Raspberry Pi、ESP32、摄像头和动画表情屏暂不包含在第一版中。

## 快速开始

### 1. 安装前置软件

安装 Python 3.11 或更高版本，以及 Ollama。

### 2. 下载默认本地模型

```bash
ollama pull qwen3:4b-instruct
```

### 3. 克隆并安装项目

```bash
git clone https://github.com/jonasnick629182-blip/open-voice-box.git
cd open-voice-box
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -e .
```

### 4. 启动

```bash
python -m open_voice_box
```

第一次进行语音识别时，Whisper 模型可能需要联网下载一次；之后识别可在本地运行。

## 可选：OpenAI 云端模式

```bash
cp .env.example .env
```

修改：

```dotenv
OVB_PROVIDER=openai
OPENAI_API_KEY=your_key_here
OVB_OPENAI_MODEL=gpt-5-mini
```

不要把 `.env` 提交到 GitHub。

应用顶部的 **Model settings** 区域可以在 Ollama 与 OpenAI 之间切换，并修改当前模型名称。OpenAI 模式仍然需要通过环境变量或 `.env` 提供 `OPENAI_API_KEY`。

## 配置项

| 变量 | 默认值 | 用途 |
| --- | --- | --- |
| `OVB_PROVIDER` | `ollama` | `ollama` 或 `openai` |
| `OVB_OLLAMA_URL` | `http://localhost:11434` | 本地 Ollama 地址 |
| `OVB_OLLAMA_MODEL` | `qwen3:4b-instruct` | 本地模型 |
| `OVB_OPENAI_MODEL` | `gpt-5-mini` | 可选云端模型 |
| `OVB_STT_MODEL` | `small` | faster-whisper 模型 |
| `OVB_TTS_VOICE` | 空 | 可选的 macOS `say` 声音 |

## 常见问题

### 麦克风权限

如果无法录音，请进入 macOS **系统设置 → 隐私与安全性 → 麦克风**，给你运行 Open Voice Box 所使用的终端或 Python 应用授予麦克风权限。

### 无法连接 Ollama

启动 Ollama，然后检查模型：

```bash
ollama list
ollama pull qwen3:4b-instruct
```

### 第一次下载语音模型失败

第一次使用本地语音识别时需要下载模型。请确认网络可用后重试；模型下载完成后，后续识别可本地执行。

## 测试

```bash
python -m pip install -e '.[dev]'
python -m pytest -q
```

## Roadmap

- 唤醒词
- 更好的多语言/本地 TTS
- 可选的长期记忆
- Linux / Raspberry Pi 验证
- ESP32 控制
- 屏幕 / 动画表情
- Skills 与智能家居

## 参与贡献

请阅读 `CONTRIBUTING.md`。

## 开源许可证

MIT
