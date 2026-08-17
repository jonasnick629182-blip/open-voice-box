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
