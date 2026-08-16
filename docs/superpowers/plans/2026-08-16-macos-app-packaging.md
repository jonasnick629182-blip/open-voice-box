# Open Voice Box macOS App Packaging Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a reproducible unsigned Apple Silicon macOS `Open Voice Box.app` for v0.2.0 that launches without a Python virtual environment while preserving the current local-first voice workflow.

**Architecture:** Keep the existing `open_voice_box.app:main` runtime path unchanged and add packaging only around it. PyInstaller will build a windowed onedir-style `.app`; a small macOS build script will generate a project icon, run PyInstaller, and structurally verify the resulting bundle. Ollama stays external and the faster-whisper model remains a runtime/first-use download.

**Tech Stack:** Python 3.11+, Tkinter, PyInstaller 6.x, Pillow for build-time icon generation, faster-whisper/CTranslate2, GitHub Actions on macOS.

## Global Constraints

- Target release is exactly `v0.2.0`.
- Release target is Apple Silicon macOS; Intel/x86_64 distribution is out of scope.
- Build `Open Voice Box.app` as a PyInstaller windowed onedir-style bundle; do not use onefile.
- Display name is exactly `Open Voice Box`.
- Bundle identifier is exactly `io.github.jonasnick629182-blip.openvoicebox`.
- Bundle version is exactly `0.2.0`.
- `NSMicrophoneUsageDescription` must explain that microphone access is required for push-to-talk voice input.
- Ollama is not bundled and remains reachable at `http://localhost:11434` by default.
- The faster-whisper model is not bundled; it remains lazy-loaded/downloaded at runtime.
- No API key or `.env` file may be embedded in the app.
- No Mac App Store work, Developer ID signing, notarization, DMG/PKG creation, Windows packaging, or Raspberry Pi packaging.
- Existing user-facing errors for missing Ollama, missing Ollama model, microphone failures, no audio, speech model load failure, and transcription failure must remain recoverable.
- Existing tests must remain green.

---

## File Structure

Files to create:

- `packaging/OpenVoiceBox.spec` — single checked-in PyInstaller bundle definition and macOS `Info.plist` metadata.
- `scripts/generate_macos_icon.py` — deterministic build-time generator for `packaging/OpenVoiceBox.icns`; no binary icon needs to be committed.
- `scripts/verify_macos_bundle.py` — standard-library structural verifier for bundle layout and plist metadata.
- `scripts/build_macos_app.sh` — one reproducible local/CI build entry point.
- `tests/test_packaging_contract.py` — lightweight configuration/version/spec contract tests that run in the normal test suite.
- `tests/test_bundle_verifier.py` — tests the bundle verifier against a fake `.app` tree without building PyInstaller output.

Files to modify:

- `pyproject.toml` — bump package version to `0.2.0`; add build-only `packaging` optional dependencies.
- `src/open_voice_box/__init__.py` — bump `__version__` to `0.2.0`.
- `.github/workflows/ci.yml` — add independent macOS packaging smoke job.
- `README.md` — add v0.2 `.app` build/run instructions, prerequisites, Gatekeeper note, and update roadmap status.
- `README_CN.md` — Chinese equivalent of the macOS `.app` instructions and Gatekeeper note.
- `CHANGELOG.md` — add the `0.2.0` packaging milestone.

Application source files such as `app.py`, `controller.py`, recorder, STT, provider, and TTS modules should not change unless a real packaged-app regression demonstrates that packaging cannot preserve the current behavior.

---

### Task 1: Lock v0.2 packaging metadata and dependency contract

**Files:**
- Create: `tests/test_packaging_contract.py`
- Modify: `pyproject.toml`
- Modify: `src/open_voice_box/__init__.py`

**Interfaces:**
- Consumes: existing Python package metadata and `open_voice_box.__version__`.
- Produces: project/package version `0.2.0` and optional dependency group `packaging` containing PyInstaller and Pillow.

- [ ] **Step 1: Write the failing packaging contract test**

Create `tests/test_packaging_contract.py`:

```python
from pathlib import Path
import re
import tomllib


ROOT = Path(__file__).resolve().parents[1]


def test_project_and_package_versions_are_0_2_0():
    pyproject = tomllib.loads((ROOT / "pyproject.toml").read_text())
    init_text = (ROOT / "src/open_voice_box/__init__.py").read_text()

    assert pyproject["project"]["version"] == "0.2.0"
    assert re.search(r'__version__\s*=\s*["\']0\.2\.0["\']', init_text)


def test_packaging_extra_contains_pyinstaller_and_pillow():
    pyproject = tomllib.loads((ROOT / "pyproject.toml").read_text())
    requirements = pyproject["project"]["optional-dependencies"]["packaging"]

    assert any(item.startswith("pyinstaller") for item in requirements)
    assert any(item.startswith("pillow") for item in requirements)
```

- [ ] **Step 2: Run the new test and confirm it fails**

Run:

```bash
python -m pytest tests/test_packaging_contract.py -q
```

Expected: FAIL because the current version is `0.1.0` and no `packaging` optional dependency group exists.

- [ ] **Step 3: Make the minimum metadata changes**

Change `pyproject.toml` to:

```toml
[project]
name = "open-voice-box"
version = "0.2.0"
# existing fields unchanged

[project.optional-dependencies]
dev = ["pytest"]
packaging = [
  "pyinstaller>=6.21,<7",
  "pillow>=11,<13",
]
```

Change `src/open_voice_box/__init__.py` to:

```python
__version__ = "0.2.0"
```

- [ ] **Step 4: Run the focused test, then the full suite**

Run:

```bash
python -m pytest tests/test_packaging_contract.py -q
python -m pytest -q
```

Expected: both PASS.

- [ ] **Step 5: Commit**

```bash
git add pyproject.toml src/open_voice_box/__init__.py tests/test_packaging_contract.py
git commit -m "chore: prepare v0.2 packaging metadata"
```

---

### Task 2: Add a deterministic macOS app icon generator

**Files:**
- Create: `scripts/generate_macos_icon.py`

**Interfaces:**
- Consumes: Pillow from the `packaging` extra and macOS `iconutil`.
- Produces: `packaging/OpenVoiceBox.icns` when executed on macOS.

- [ ] **Step 1: Create the icon generator**

Create `scripts/generate_macos_icon.py` with one deterministic source image and the standard macOS iconset sizes:

```python
from pathlib import Path
import shutil
import subprocess
import tempfile

from PIL import Image, ImageDraw


ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "packaging" / "OpenVoiceBox.icns"


def render_icon(size: int = 1024) -> Image.Image:
    image = Image.new("RGBA", (size, size), (28, 30, 36, 255))
    draw = ImageDraw.Draw(image)

    margin = size // 16
    radius = size // 5
    draw.rounded_rectangle(
        (margin, margin, size - margin, size - margin),
        radius=radius,
        fill=(35, 39, 47, 255),
    )

    stroke = max(8, size // 24)
    left = int(size * 0.38)
    top = int(size * 0.20)
    right = int(size * 0.62)
    bottom = int(size * 0.60)
    draw.rounded_rectangle(
        (left, top, right, bottom),
        radius=(right - left) // 2,
        outline=(245, 247, 250, 255),
        width=stroke,
    )
    draw.arc(
        (int(size * 0.29), int(size * 0.42), int(size * 0.71), int(size * 0.76)),
        0,
        180,
        fill=(245, 247, 250, 255),
        width=stroke,
    )
    draw.line(
        (size // 2, int(size * 0.76), size // 2, int(size * 0.86)),
        fill=(245, 247, 250, 255),
        width=stroke,
    )
    draw.line(
        (int(size * 0.40), int(size * 0.86), int(size * 0.60), int(size * 0.86)),
        fill=(245, 247, 250, 255),
        width=stroke,
    )
    return image


def build_icns(output: Path = OUTPUT) -> Path:
    if shutil.which("iconutil") is None:
        raise RuntimeError("iconutil is required and is only available on macOS")

    output.parent.mkdir(parents=True, exist_ok=True)
    master = render_icon(1024)
    sizes = {
        "icon_16x16.png": 16,
        "icon_16x16@2x.png": 32,
        "icon_32x32.png": 32,
        "icon_32x32@2x.png": 64,
        "icon_128x128.png": 128,
        "icon_128x128@2x.png": 256,
        "icon_256x256.png": 256,
        "icon_256x256@2x.png": 512,
        "icon_512x512.png": 512,
        "icon_512x512@2x.png": 1024,
    }

    with tempfile.TemporaryDirectory() as temp_dir:
        iconset = Path(temp_dir) / "OpenVoiceBox.iconset"
        iconset.mkdir()
        for filename, pixels in sizes.items():
            master.resize((pixels, pixels), Image.Resampling.LANCZOS).save(
                iconset / filename
            )
        subprocess.run(
            ["iconutil", "-c", "icns", str(iconset), "-o", str(output)],
            check=True,
        )
    return output


if __name__ == "__main__":
    print(build_icns())
```

- [ ] **Step 2: Install packaging dependencies and generate the icon**

Run on macOS:

```bash
python -m pip install -e '.[dev,packaging]'
python scripts/generate_macos_icon.py
```

Expected: `packaging/OpenVoiceBox.icns` is created and `file packaging/OpenVoiceBox.icns` reports an Apple icon image/container rather than an error.

- [ ] **Step 3: Do not commit the generated binary**

Add this exact line to `.gitignore` only if Git reports the generated file as untracked:

```gitignore
packaging/OpenVoiceBox.icns
```

The generator is the source of truth; the binary `.icns` remains build output.

- [ ] **Step 4: Re-run the full unit suite**

```bash
python -m pytest -q
```

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add scripts/generate_macos_icon.py .gitignore
git commit -m "build: generate macOS app icon"
```

---

### Task 3: Define the PyInstaller app bundle and test its static contract

**Files:**
- Create: `packaging/OpenVoiceBox.spec`
- Modify: `tests/test_packaging_contract.py`

**Interfaces:**
- Consumes: `src/open_voice_box/__main__.py`, generated `packaging/OpenVoiceBox.icns`, installed runtime dependencies.
- Produces: PyInstaller definition for `dist/Open Voice Box.app`.

- [ ] **Step 1: Add a failing spec-contract test**

Append to `tests/test_packaging_contract.py`:

```python
def test_spec_declares_required_macos_bundle_metadata():
    spec = (ROOT / "packaging/OpenVoiceBox.spec").read_text()

    required = (
        'name="Open Voice Box.app"',
        'bundle_identifier="io.github.jonasnick629182-blip.openvoicebox"',
        'version="0.2.0"',
        '"NSMicrophoneUsageDescription"',
        '"CFBundleDisplayName": "Open Voice Box"',
        'console=False',
        'collect_data_files("faster_whisper")',
        'collect_dynamic_libs("ctranslate2")',
    )
    for text in required:
        assert text in spec
```

- [ ] **Step 2: Run it and verify the expected failure**

```bash
python -m pytest tests/test_packaging_contract.py::test_spec_declares_required_macos_bundle_metadata -q
```

Expected: FAIL because `packaging/OpenVoiceBox.spec` does not exist.

- [ ] **Step 3: Create the focused PyInstaller spec**

Create `packaging/OpenVoiceBox.spec`:

```python
from pathlib import Path

from PyInstaller.utils.hooks import collect_data_files, collect_dynamic_libs


ROOT = Path(SPEC).resolve().parent.parent
ENTRY = ROOT / "src/open_voice_box/__main__.py"
ICON = ROOT / "packaging/OpenVoiceBox.icns"

datas = collect_data_files("faster_whisper")
binaries = collect_dynamic_libs("ctranslate2")

analysis = Analysis(
    [str(ENTRY)],
    pathex=[str(ROOT / "src")],
    binaries=binaries,
    datas=datas,
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
)
pyz = PYZ(analysis.pure)

exe = EXE(
    pyz,
    analysis.scripts,
    [],
    exclude_binaries=True,
    name="Open Voice Box",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

collection = COLLECT(
    exe,
    analysis.binaries,
    analysis.datas,
    strip=False,
    upx=False,
    name="Open Voice Box",
)

app = BUNDLE(
    collection,
    name="Open Voice Box.app",
    icon=str(ICON),
    bundle_identifier="io.github.jonasnick629182-blip.openvoicebox",
    version="0.2.0",
    info_plist={
        "CFBundleDisplayName": "Open Voice Box",
        "NSHighResolutionCapable": True,
        "NSMicrophoneUsageDescription": (
            "Open Voice Box needs microphone access to record push-to-talk voice input."
        ),
    },
)
```

Do not add broad `collect_all()` calls. The first build should use only the targeted faster-whisper data and CTranslate2 dynamic libraries.

- [ ] **Step 4: Run the contract test and full suite**

```bash
python -m pytest tests/test_packaging_contract.py -q
python -m pytest -q
```

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add packaging/OpenVoiceBox.spec tests/test_packaging_contract.py
git commit -m "build: define macOS PyInstaller bundle"
```

---

### Task 4: Add a structural bundle verifier and reproducible build command

**Files:**
- Create: `scripts/verify_macos_bundle.py`
- Create: `tests/test_bundle_verifier.py`
- Create: `scripts/build_macos_app.sh`

**Interfaces:**
- Produces: `verify_bundle(path: Path) -> None` and one build command `bash scripts/build_macos_app.sh`.
- The verifier raises `AssertionError` with an actionable message for a malformed bundle.

- [ ] **Step 1: Write failing verifier tests**

Create `tests/test_bundle_verifier.py`:

```python
from pathlib import Path
import plistlib

import pytest

from scripts.verify_macos_bundle import verify_bundle


def make_bundle(tmp_path: Path, *, microphone_key: bool = True) -> Path:
    bundle = tmp_path / "Open Voice Box.app"
    contents = bundle / "Contents"
    macos = contents / "MacOS"
    macos.mkdir(parents=True)
    executable = macos / "Open Voice Box"
    executable.write_bytes(b"placeholder")

    info = {
        "CFBundleDisplayName": "Open Voice Box",
        "CFBundleIdentifier": "io.github.jonasnick629182-blip.openvoicebox",
        "CFBundleShortVersionString": "0.2.0",
        "CFBundleExecutable": "Open Voice Box",
    }
    if microphone_key:
        info["NSMicrophoneUsageDescription"] = (
            "Open Voice Box needs microphone access to record push-to-talk voice input."
        )
    with (contents / "Info.plist").open("wb") as handle:
        plistlib.dump(info, handle)
    return bundle


def test_verify_bundle_accepts_expected_structure(tmp_path):
    verify_bundle(make_bundle(tmp_path))


def test_verify_bundle_requires_microphone_usage_description(tmp_path):
    with pytest.raises(AssertionError, match="NSMicrophoneUsageDescription"):
        verify_bundle(make_bundle(tmp_path, microphone_key=False))
```

- [ ] **Step 2: Run and confirm import failure**

```bash
python -m pytest tests/test_bundle_verifier.py -q
```

Expected: FAIL because `scripts.verify_macos_bundle` does not exist.

- [ ] **Step 3: Implement the verifier**

Create `scripts/verify_macos_bundle.py`:

```python
from pathlib import Path
import plistlib
import sys


EXPECTED_ID = "io.github.jonasnick629182-blip.openvoicebox"
EXPECTED_VERSION = "0.2.0"
EXPECTED_NAME = "Open Voice Box"


def verify_bundle(bundle: Path) -> None:
    assert bundle.is_dir(), f"Bundle not found: {bundle}"
    plist_path = bundle / "Contents/Info.plist"
    assert plist_path.is_file(), f"Missing Info.plist: {plist_path}"

    with plist_path.open("rb") as handle:
        info = plistlib.load(handle)

    assert info.get("CFBundleDisplayName") == EXPECTED_NAME
    assert info.get("CFBundleIdentifier") == EXPECTED_ID
    assert info.get("CFBundleShortVersionString") == EXPECTED_VERSION
    microphone = info.get("NSMicrophoneUsageDescription", "").strip()
    assert microphone, "Missing NSMicrophoneUsageDescription"

    executable_name = info.get("CFBundleExecutable")
    assert executable_name, "Missing CFBundleExecutable"
    executable = bundle / "Contents/MacOS" / executable_name
    assert executable.is_file(), f"Missing bundle executable: {executable}"


if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit("usage: verify_macos_bundle.py <path-to.app>")
    verify_bundle(Path(sys.argv[1]))
    print(f"verified: {sys.argv[1]}")
```

- [ ] **Step 4: Verify tests pass**

```bash
python -m pytest tests/test_bundle_verifier.py -q
```

Expected: PASS.

- [ ] **Step 5: Add the one-command macOS build script**

Create `scripts/build_macos_app.sh`:

```bash
#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

if [[ "$(uname -s)" != "Darwin" ]]; then
  echo "Open Voice Box .app packaging requires macOS." >&2
  exit 1
fi

python scripts/generate_macos_icon.py
python -m PyInstaller --clean --noconfirm packaging/OpenVoiceBox.spec
python scripts/verify_macos_bundle.py "dist/Open Voice Box.app"
```

- [ ] **Step 6: Run the first real build**

```bash
python -m pip install -e '.[dev,packaging]'
bash scripts/build_macos_app.sh
```

Expected end state:

```text
dist/Open Voice Box.app
verified: dist/Open Voice Box.app
```

If PyInstaller reports a missing faster-whisper/CTranslate2 resource, fix only the named missing package by adding a targeted `collect_data_files()` or `collect_dynamic_libs()` call to the spec, then rerun this exact command. Do not use `collect_all()` as a blanket workaround.

- [ ] **Step 7: Run all tests after a successful build**

```bash
python -m pytest -q
```

Expected: PASS.

- [ ] **Step 8: Commit**

```bash
git add scripts/build_macos_app.sh scripts/verify_macos_bundle.py tests/test_bundle_verifier.py packaging/OpenVoiceBox.spec
git commit -m "build: add reproducible macOS app build"
```

---

### Task 5: Add macOS packaging smoke coverage to GitHub Actions

**Files:**
- Modify: `.github/workflows/ci.yml`

**Interfaces:**
- Consumes: `bash scripts/build_macos_app.sh`.
- Produces: an independent `package-macos` CI job that proves the `.app` can be built and structurally verified on a hosted macOS runner.

- [ ] **Step 1: Extend CI with a packaging job**

Keep the existing `test` job unchanged and add:

```yaml
  package-macos:
    runs-on: macos-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.11"
      - run: python -m pip install --upgrade pip
      - run: python -m pip install -e '.[dev,packaging]'
      - run: bash scripts/build_macos_app.sh
      - run: python scripts/verify_macos_bundle.py "dist/Open Voice Box.app"
```

Do not upload the CI-built `.app` as the v0.2 release artifact because the release target must be the manually accepted Apple Silicon build; CI is only a build/structure smoke test.

- [ ] **Step 2: Validate YAML and local test suite**

Run:

```bash
python - <<'PY'
from pathlib import Path
text = Path('.github/workflows/ci.yml').read_text()
assert 'package-macos:' in text
assert 'bash scripts/build_macos_app.sh' in text
assert '.[dev,packaging]' in text
print('CI packaging contract OK')
PY
python -m pytest -q
```

Expected: contract check prints `CI packaging contract OK`; tests PASS.

- [ ] **Step 3: Commit**

```bash
git add .github/workflows/ci.yml
git commit -m "ci: smoke test macOS app packaging"
```

---

### Task 6: Document v0.2 app usage, prerequisites, and unsigned-app behavior

**Files:**
- Modify: `README.md`
- Modify: `README_CN.md`
- Modify: `CHANGELOG.md`

**Interfaces:**
- Produces: user-facing instructions that clearly separate source/developer setup from the new `.app` build and explain that Ollama and the model are still prerequisites.

- [ ] **Step 1: Update the English README**

Change the top release callout to:

```markdown
> **V0.2:** macOS-first, push-to-talk, Ollama-first, with a reproducible unsigned `.app` build for Apple Silicon.
```

Add this section before the existing source `Quick start` section:

```markdown
## macOS app build (v0.2)

V0.2 can be packaged as an unsigned Apple Silicon macOS application. Ollama remains an external prerequisite and the faster-whisper model is downloaded on first speech use.

### Prerequisites

- Apple Silicon Mac
- Ollama installed and running
- Default local model pulled with `ollama pull qwen3:4b-instruct`
- Python 3.11+ is required to build the `.app`, but not to launch the finished bundle

### Build

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -e '.[dev,packaging]'
bash scripts/build_macos_app.sh
```

The generated application is:

```text
dist/Open Voice Box.app
```

Open it from Finder or run:

```bash
open "dist/Open Voice Box.app"
```

### Unsigned app / Gatekeeper

V0.2 is not signed or notarized. On first launch, macOS may block the app. In Finder, Control-click **Open Voice Box.app**, choose **Open**, and confirm the prompt. Do not disable Gatekeeper globally.

### Microphone permission

The app declares its microphone usage purpose in its macOS bundle. When prompted, allow **Open Voice Box** under **System Settings → Privacy & Security → Microphone**.
```

Keep the existing Python/source Quick Start after this section for contributors.

- [ ] **Step 2: Update the Chinese README with equivalent meaning**

Add a `## macOS 应用打包（v0.2）` section covering exactly these points:

```markdown
- 目标是 Apple Silicon Mac。
- Ollama 仍需单独安装并运行。
- 默认模型仍需执行 `ollama pull qwen3:4b-instruct`。
- Whisper 模型第一次语音识别时下载，不打进 `.app`。
- 构建命令是 `bash scripts/build_macos_app.sh`。
- 产物是 `dist/Open Voice Box.app`。
- v0.2 未签名、未公证；首次启动如果被 macOS 拦截，使用 Finder 中“按住 Control 点击 → 打开”，不要全局关闭 Gatekeeper。
- 麦克风授权对象应显示为 Open Voice Box。
```

- [ ] **Step 3: Add the v0.2.0 changelog entry**

Insert above `0.1.0`:

```markdown
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
```

- [ ] **Step 4: Verify docs contain the critical safety/usage statements**

```bash
python - <<'PY'
from pathlib import Path
readme = Path('README.md').read_text()
cn = Path('README_CN.md').read_text()
assert 'dist/Open Voice Box.app' in readme
assert 'Do not disable Gatekeeper globally' in readme
assert 'ollama pull qwen3:4b-instruct' in readme
assert '不要全局关闭 Gatekeeper' in cn
assert 'dist/Open Voice Box.app' in cn
print('documentation contract OK')
PY
python -m pytest -q
```

Expected: `documentation contract OK`; tests PASS.

- [ ] **Step 5: Commit**

```bash
git add README.md README_CN.md CHANGELOG.md
git commit -m "docs: document v0.2 macOS app build"
```

---

### Task 7: Perform Apple Silicon acceptance testing on the real Mac

**Files:**
- No source files expected unless a reproducible packaged-app regression is found.

**Interfaces:**
- Consumes: `dist/Open Voice Box.app` built on the user's Apple Silicon Mac, Ollama, `qwen3:4b-instruct`.
- Produces: objective acceptance evidence for Issue #4.

- [ ] **Step 1: Start from a clean build**

```bash
rm -rf build dist packaging/OpenVoiceBox.icns
python -m pip install -e '.[dev,packaging]'
bash scripts/build_macos_app.sh
```

Expected: `dist/Open Voice Box.app` exists and verifier passes.

- [ ] **Step 2: Confirm the release binary is Apple Silicon**

```bash
file "dist/Open Voice Box.app/Contents/MacOS/Open Voice Box"
```

Expected: output contains `arm64`. If the executable is not arm64, do not publish it as the v0.2 release artifact.

- [ ] **Step 3: Inspect bundle metadata**

```bash
plutil -p "dist/Open Voice Box.app/Contents/Info.plist"
```

Confirm all of these are present:

```text
CFBundleDisplayName = Open Voice Box
CFBundleIdentifier = io.github.jonasnick629182-blip.openvoicebox
CFBundleShortVersionString = 0.2.0
NSMicrophoneUsageDescription = Open Voice Box needs microphone access to record push-to-talk voice input.
```

- [ ] **Step 4: Launch as a GUI app**

Open from Finder by double-clicking, or:

```bash
open "dist/Open Voice Box.app"
```

Expected: the Open Voice Box window appears and no Terminal window is required for normal use.

- [ ] **Step 5: Verify microphone permission**

Press **Speak** once. If macOS prompts, allow microphone access. Then verify **System Settings → Privacy & Security → Microphone** lists **Open Voice Box** and it is enabled.

- [ ] **Step 6: Verify Chinese end-to-end turn**

With Ollama running and `qwen3:4b-instruct` installed, press **Speak**, say a short Chinese sentence, stop recording, and confirm:

```text
recording → Chinese transcript → Ollama answer → visible answer → audible macOS voice
```

- [ ] **Step 7: Verify English end-to-end turn**

Repeat with a short English sentence and confirm the same full path.

- [ ] **Step 8: Verify missing-model recovery**

In the UI set the Ollama model field to:

```text
test-missing-model
```

Apply it, perform a turn, and confirm the UI shows a message containing:

```text
ollama pull test-missing-model
```

Then restore `qwen3:4b-instruct`.

- [ ] **Step 9: Verify Ollama-unavailable recovery**

Quit Ollama, perform a turn, and confirm the UI reports that Ollama is not reachable instead of crashing. Restart Ollama before continuing.

- [ ] **Step 10: Verify speech-model load failure remains friendly**

Temporarily set a deliberately invalid STT model for LaunchServices:

```bash
launchctl setenv OVB_STT_MODEL __open_voice_box_missing_model__
open "dist/Open Voice Box.app"
```

Attempt a speech turn and confirm the UI reports that the speech model could not be loaded and suggests checking the network/retrying. Then clean up:

```bash
launchctl unsetenv OVB_STT_MODEL
```

Close and reopen the app normally after clearing the environment value.

- [ ] **Step 11: Re-run automated regression tests**

```bash
python -m pytest -q
```

Expected: PASS.

- [ ] **Step 12: Record the acceptance result on Issue #4**

Add a GitHub comment containing the tested Mac architecture, the successful build command, test-suite result, Chinese/English voice round-trip result, microphone permission result, and each recoverable error case. Do not claim a case passed unless it was actually observed.

---

### Task 8: PR, CI, merge, Issue closure, and v0.2.0 release

**Files:**
- No additional source changes expected.

**Interfaces:**
- Produces: merged maintenance cycle and a real v0.2.0 release only after CI + Apple Silicon acceptance pass.

- [ ] **Step 1: Final local verification**

```bash
python -m pytest -q
bash scripts/build_macos_app.sh
python scripts/verify_macos_bundle.py "dist/Open Voice Box.app"
```

Expected: all commands succeed.

- [ ] **Step 2: Open the pull request**

Use title:

```text
feat: package Open Voice Box as a macOS app
```

Use body:

```markdown
## Summary
- add reproducible PyInstaller `Open Voice Box.app` packaging
- add macOS metadata and microphone usage description
- add deterministic app icon generation and bundle verification
- add macOS packaging CI smoke test
- document unsigned Apple Silicon app usage

Closes #4

## Verification
- `python -m pytest -q`
- `bash scripts/build_macos_app.sh`
- Apple Silicon manual Chinese/English voice round-trip
- microphone permission verified as Open Voice Box
- missing Ollama/model and speech-model failure paths verified
```

- [ ] **Step 3: Wait for both CI jobs to pass**

Required status:

```text
test: success
package-macos: success
```

Do not merge while either job is failing.

- [ ] **Step 4: Review the PR diff for scope**

Confirm it does not contain unrelated UI redesign, wake-word work, persistence, hardware features, `.env`, API keys, model weights, `build/`, `dist/`, generated `.icns`, or audio recordings.

- [ ] **Step 5: Merge the PR**

Use squash or the repository's normal merge method. Confirm Issue #4 closes through `Closes #4` only after the acceptance comment is present.

- [ ] **Step 6: Build the release artifact from updated `main` on Apple Silicon**

```bash
git checkout main
git pull --ff-only
rm -rf build dist packaging/OpenVoiceBox.icns
python -m pip install -e '.[dev,packaging]'
bash scripts/build_macos_app.sh
file "dist/Open Voice Box.app/Contents/MacOS/Open Voice Box"
```

Expected: verifier passes and `file` contains `arm64`.

- [ ] **Step 7: Zip the `.app` without flattening the bundle**

```bash
ditto -c -k --sequesterRsrc --keepParent \
  "dist/Open Voice Box.app" \
  "dist/Open-Voice-Box-v0.2.0-macos-arm64.zip"
```

- [ ] **Step 8: Publish v0.2.0**

Create tag `v0.2.0` from `main`, mark it as Latest (not pre-release), attach `Open-Voice-Box-v0.2.0-macos-arm64.zip`, and use release notes that explicitly state:

```text
- Apple Silicon macOS development build
- unsigned and not notarized
- Ollama must be installed separately
- qwen3:4b-instruct must be pulled separately
- faster-whisper model downloads on first speech use
- Finder Control-click → Open may be required on first launch
```

Do not describe the app as signed, notarized, App Store ready, Intel-compatible, or fully offline.

---

## Plan Self-Review

### Spec coverage

- Apple Silicon `.app`: Tasks 3, 4, 7, 8.
- Windowed onedir PyInstaller architecture: Task 3.
- Python/runtime bundling: Tasks 3 and 4.
- Ollama external: Global constraints, Tasks 6–8.
- Whisper runtime download: Global constraints, Tasks 3, 6, 7.
- Existing provider/model selector preserved: no app-path fork; Task 7 validates runtime behavior.
- App name/version/bundle identifier/microphone description: Tasks 1, 3, 4, 7.
- App icon: Task 2.
- Reproducible build: Task 4.
- CI packaging smoke: Task 5.
- Expected environment errors remain understandable: Task 7.
- Gatekeeper guidance: Task 6.
- Real Chinese + English acceptance: Task 7.
- Release workflow: Task 8.
- Signing/notarization/DMG/Intel/hardware excluded: Global constraints and Task 8 scope review.

### Placeholder scan

No `TBD`, `TODO`, `implement later`, unspecified validation, or unnamed files remain in this plan.

### Type/name consistency

- Bundle path is consistently `dist/Open Voice Box.app`.
- Bundle executable is consistently `Open Voice Box`.
- Bundle identifier is consistently `io.github.jonasnick629182-blip.openvoicebox`.
- Version is consistently `0.2.0` / release tag `v0.2.0`.
- Build entry point is consistently `bash scripts/build_macos_app.sh`.
- Structural verifier is consistently `verify_bundle(path: Path) -> None`.
