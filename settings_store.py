"""Persistent user settings: custom aliases and toggles."""
from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

CONFIG_DIR = Path(os.environ.get("APPDATA", Path.home())) / "SpotlightLauncher"
CONFIG_FILE = CONFIG_DIR / "settings.json"

DEFAULTS: dict[str, Any] = {
    "aliases": {},                 # name -> command string (run via cmd /c)
    "launch_stats": {},            # item key -> usage metadata for local ranking
    "hotkey": "Alt+Space",
    "launch_at_startup": False,
    "include_apps": True,
    "include_quick_actions": True,
    "include_recent_files": True,
    "full_file_scan": False,
    "confirm_system_actions": True,
    "max_results": 8,
}


def load() -> dict[str, Any]:
    if not CONFIG_FILE.exists():
        return dict(DEFAULTS)
    try:
        data = json.loads(CONFIG_FILE.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return dict(DEFAULTS)
    merged = dict(DEFAULTS)
    merged.update(data)
    return merged


def save(data: dict[str, Any]) -> None:
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    CONFIG_FILE.write_text(json.dumps(data, indent=2), encoding="utf-8")
