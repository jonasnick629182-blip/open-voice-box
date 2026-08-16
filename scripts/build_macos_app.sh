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
