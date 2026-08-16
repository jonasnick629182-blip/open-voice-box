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


def test_build_script_runs_icon_pyinstaller_and_verifier():
    script = (ROOT / "scripts/build_macos_app.sh").read_text()

    assert 'python scripts/generate_macos_icon.py' in script
    assert 'python -m PyInstaller --clean --noconfirm packaging/OpenVoiceBox.spec' in script
    assert 'python scripts/verify_macos_bundle.py "dist/Open Voice Box.app"' in script
    assert 'uname -s' in script
