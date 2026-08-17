# Open Voice Box

一个本地优先的中英双语语音 AI 助手，V0.2 继续以 macOS 为第一支持平台。按下按钮，用中文或英文说话，AI 会生成回答并通过系统语音朗读。

> **V0.2：** macOS-first、按键说话、Ollama-first，并提供可复现的 Apple Silicon 未签名 `.app` 打包流程。

## 为什么做 Open Voice Box？

- **本地优先：** 默认使用 Ollama，不要求付费 API Key。
- **中英双语：** 本地语音识别自动判断中文或英文。
- **语音输入与播报：** 麦克风输入、可见文字回答和系统语音朗读。
- **可选云端模式：** 可以通过环境变量切换到 OpenAI。
- **方便扩展：** LLM、语音识别、录音和语音播报互相隔离，后续可以继续接入硬件。

## V0.1

V0.1 是第一个可工作的原型，已经在 Apple Silicon Mac 上完成中英文真实语音回合、麦克风权限、Ollama 不可用、模型缺失和临时录音清理等验证。

## V0.2 macOS `.app` 打包

V0.2 可以打包成 Apple Silicon macOS 应用。**Ollama 不会被打进 `.app`**，仍需要单独安装；`faster-whisper` 的语音模型也不会被内置，第一次进行语音识别时仍可能需要联网下载。

### 前置条件

- Apple Silicon Mac
- 已安装并启动 Ollama
- 已执行 `ollama pull qwen3:4b-instruct`
- 构建 `.app` 时需要 Python 3.11+；构建完成后的 `.app` 本身不要求用户再创建 Python 虚拟环境

### 构建

```bash
git clone https://github.com/jonasnick629182-blip/open-voice-box.git
cd open-voice-box
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -e '.[dev,packaging]'
bash scripts/build_macos_app.sh
```

构建完成后应用位于：

```text
dist/Open Voice Box.app
```

可以在 Finder 里双击，也可以执行：

```bash
open "dist/Open Voice Box.app"
```

### 未签名应用 / Gatekeeper

V0.2 当前没有 Apple Developer ID 签名，也没有 notarization（公证）。macOS 第一次启动时可能阻止打开。可以在 Finder 中按住 Control 点击 **Open Voice Box.app** → 选择 **打开** → 确认。

**不要为了运行本项目而全局关闭 Gatekeeper。**

### 麦克风权限

`.app` 已在 macOS Bundle 中声明麦克风用途。系统询问时，在 **系统设置 → 隐私与安全性 → 麦克风** 中允许 **Open Voice Box** 使用麦克风。

## 从源码快速开始

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

使用 V0.2 `.app` 时，在 macOS **系统设置 → 隐私与安全性 → 麦克风** 中允许 **Open Voice Box**。如果是从源码运行，权限项可能显示为你使用的终端或 Python。

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

macOS 打包烟雾测试：

```bash
python -m pip install -e '.[dev,packaging]'
bash scripts/build_macos_app.sh
python scripts/verify_macos_bundle.py "dist/Open Voice Box.app"
```

## Roadmap

当前 roadmap：

- #2：唤醒词模式
- #3：改善实时转写、VAD 和静音处理
- #4：将 Open Voice Box 打包成独立 macOS `.app`

长期方向：

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
