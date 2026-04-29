"""Build script for the Utility Win Windows installer."""
from __future__ import annotations

import sys

from cx_Freeze import Executable, setup


APP_NAME = "Utility Win"
VERSION = "1.0.0"
DESCRIPTION = "A premium Spotlight-style utility launcher for Windows."
UPGRADE_CODE = "{8ED6A4FA-7D4A-4D62-BA3A-34C7AF69C101}"


build_exe_options = {
    "includes": ["PyQt6.QtCore", "PyQt6.QtGui", "PyQt6.QtWidgets"],
    "include_files": ["UtilityWin.ico"],
    "excludes": [
        "tkinter",
        "unittest",
        "test",
        "PyQt6.QtBluetooth",
        "PyQt6.QtDBus",
        "PyQt6.QtDesigner",
        "PyQt6.QtHelp",
        "PyQt6.QtMultimedia",
        "PyQt6.QtNetwork",
        "PyQt6.QtNfc",
        "PyQt6.QtOpenGL",
        "PyQt6.QtPdf",
        "PyQt6.QtPositioning",
        "PyQt6.QtQml",
        "PyQt6.QtQuick",
        "PyQt6.QtSql",
        "PyQt6.QtSvg",
        "PyQt6.QtTest",
        "PyQt6.QtWebChannel",
        "PyQt6.QtWebSockets",
        "PyQt6.uic",
    ],
    "optimize": 2,
}

bdist_msi_options = {
    "upgrade_code": UPGRADE_CODE,
    "add_to_path": False,
    "initial_target_dir": rf"[ProgramFilesFolder]\{APP_NAME}",
    "summary_data": {
        "author": "Utility Win contributors",
        "comments": DESCRIPTION,
        "keywords": "launcher, productivity, windows, spotlight",
    },
}

base = "gui" if sys.platform == "win32" else None

executables = [
    Executable(
        "main.py",
        base=base,
        target_name="UtilityWin.exe",
        icon="UtilityWin.ico",
        shortcut_name=APP_NAME,
        shortcut_dir="DesktopFolder",
    )
]

setup(
    name=APP_NAME,
    version=VERSION,
    description=DESCRIPTION,
    long_description=(
        "Utility Win is a fast Windows tray launcher with global hotkey access, "
        "fuzzy search for apps and user files, quick system actions, aliases, "
        "settings, and a polished dark interface."
    ),
    options={"build_exe": build_exe_options, "bdist_msi": bdist_msi_options},
    executables=executables,
)
