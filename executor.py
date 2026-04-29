"""Executes a chosen Item: launches apps/files, runs quick actions, or aliases."""
from __future__ import annotations

import ctypes
import os
import subprocess
import winreg
from pathlib import Path

from indexer import Item


def execute(item: Item, aliases: dict[str, str]) -> None:
    if item.kind in ("app", "recent"):
        _open_path(item.payload)
    elif item.kind == "action":
        _run_action(item.payload)
    elif item.kind == "alias":
        cmd = aliases.get(item.payload, "").strip()
        if cmd:
            _run_shell(cmd)


def _open_path(path: str) -> None:
    # os.startfile resolves .lnk shortcuts and launches associated handlers.
    os.startfile(path)  # type: ignore[attr-defined]


def _run_shell(command: str) -> None:
    # Detached shell so the launcher doesn't block on long-running aliases.
    DETACHED = 0x00000008
    subprocess.Popen(
        ["cmd.exe", "/c", command],
        creationflags=DETACHED,
        close_fds=True,
    )


def _run_action(action_id: str) -> None:
    handler = _ACTIONS.get(action_id)
    if handler is not None:
        handler()


# --- Action implementations ---------------------------------------------------

def _empty_recycle_bin() -> None:
    SHERB_NOCONFIRMATION = 0x00000001
    SHERB_NOPROGRESSUI   = 0x00000002
    SHERB_NOSOUND        = 0x00000004
    ctypes.windll.shell32.SHEmptyRecycleBinW(
        None, None,
        SHERB_NOCONFIRMATION | SHERB_NOPROGRESSUI | SHERB_NOSOUND,
    )


def _toggle_dark_mode() -> None:
    key_path = r"Software\Microsoft\Windows\CurrentVersion\Themes\Personalize"
    with winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path, 0,
                        winreg.KEY_READ | winreg.KEY_WRITE) as key:
        try:
            current, _ = winreg.QueryValueEx(key, "AppsUseLightTheme")
        except FileNotFoundError:
            current = 1
        new_val = 0 if current else 1
        winreg.SetValueEx(key, "AppsUseLightTheme",   0, winreg.REG_DWORD, new_val)
        winreg.SetValueEx(key, "SystemUsesLightTheme", 0, winreg.REG_DWORD, new_val)


def _lock() -> None:
    ctypes.windll.user32.LockWorkStation()


def _open_downloads() -> None:
    os.startfile(str(Path.home() / "Downloads"))  # type: ignore[attr-defined]


def _open_documents() -> None:
    os.startfile(str(Path.home() / "Documents"))  # type: ignore[attr-defined]


def _open_this_pc() -> None:
    os.startfile("shell:MyComputerFolder")  # type: ignore[attr-defined]


def _open_file_explorer() -> None:
    os.startfile("explorer.exe")  # type: ignore[attr-defined]


def _open_desktop() -> None:
    os.startfile(str(Path.home() / "Desktop"))  # type: ignore[attr-defined]


def _shutdown() -> None:
    subprocess.Popen(["shutdown", "/s", "/t", "0"])


def _restart() -> None:
    subprocess.Popen(["shutdown", "/r", "/t", "0"])


def _signout() -> None:
    subprocess.Popen(["shutdown", "/l"])


_ACTIONS = {
    "empty_recycle_bin": _empty_recycle_bin,
    "toggle_dark_mode":  _toggle_dark_mode,
    "lock":              _lock,
    "open_downloads":    _open_downloads,
    "open_documents":    _open_documents,
    "open_this_pc":      _open_this_pc,
    "open_file_explorer": _open_file_explorer,
    "open_desktop":      _open_desktop,
    "shutdown":          _shutdown,
    "restart":           _restart,
    "signout":           _signout,
}
