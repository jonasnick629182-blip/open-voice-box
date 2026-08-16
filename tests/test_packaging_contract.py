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
