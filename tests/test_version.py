"""Guard against version drift: every place that declares SPECTRA's version must agree."""
import json
import re
from pathlib import Path

from spectra import __version__

ROOT = Path(__file__).resolve().parent.parent


def _match(pattern: str, path: str) -> str:
    text = (ROOT / path).read_text(encoding="utf-8")
    found = re.search(pattern, text, re.MULTILINE)
    assert found, f"no version found in {path}"
    return found.group(1)


def test_pyproject_matches_package_version():
    assert _match(r'^version\s*=\s*"([^"]+)"', "pyproject.toml") == __version__


def test_setup_cfg_matches_package_version():
    assert _match(r"^version\s*=\s*(\S+)", "setup.cfg") == __version__


def test_web_package_json_matches_package_version():
    package = json.loads((ROOT / "web" / "package.json").read_text(encoding="utf-8"))
    assert package["version"] == __version__


def test_web_package_lock_matches_package_version():
    lock = json.loads((ROOT / "web" / "package-lock.json").read_text(encoding="utf-8"))
    assert lock["version"] == __version__
    assert lock["packages"][""]["version"] == __version__
