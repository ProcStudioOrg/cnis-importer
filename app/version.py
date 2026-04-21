import json
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent
_VERSION_FILE = _ROOT / "VERSION"
_BUILD_INFO_FILE = _ROOT / ".build-info"


def _read_version() -> str:
    try:
        return _VERSION_FILE.read_text().strip()
    except FileNotFoundError:
        return "0.0.0"


def _read_build_info() -> dict:
    try:
        return json.loads(_BUILD_INFO_FILE.read_text())
    except (FileNotFoundError, json.JSONDecodeError):
        return {"git_sha": "dev", "built_at": None}


VERSION = _read_version()


def get_version_info() -> dict:
    build = _read_build_info()
    return {
        "version": VERSION,
        "git_sha": build.get("git_sha", "dev"),
        "built_at": build.get("built_at"),
    }
