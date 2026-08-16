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
