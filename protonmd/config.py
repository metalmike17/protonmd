"""Tiny user settings file (~/.config/protonmd/config.json)."""
import json
import os
from pathlib import Path


def _path():
    base = os.environ.get("XDG_CONFIG_HOME") or str(Path.home() / ".config")
    return Path(base) / "protonmd" / "config.json"


def load():
    try:
        data = json.loads(_path().read_text())
        return data if isinstance(data, dict) else {}
    except (OSError, ValueError):
        return {}


def save(data):
    p = _path()
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(data, indent=2))


def hidden_libraries():
    """Real paths of Steam libraries the user chose to hide."""
    return set(load().get("hidden_libraries", []))


def set_hidden_libraries(paths):
    data = load()
    data["hidden_libraries"] = sorted(set(paths))
    save(data)
