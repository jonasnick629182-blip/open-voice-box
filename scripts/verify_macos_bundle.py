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
