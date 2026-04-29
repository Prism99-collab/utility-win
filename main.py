"""Entry point: wires hotkey, index, executor, UI, and tray into one app."""
from __future__ import annotations

import ctypes
import sys
import traceback
import winreg
from pathlib import Path

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QApplication, QMessageBox

from app_icon import make_app_icon
import settings_store
from executor import execute as execute_item
from hotkey import HotkeyBridge
from indexer import Index, Item
from tray import Tray
from ui import SearchBar, SettingsDialog


_mutex_handle = None
ERROR_ALREADY_EXISTS = 183


class Launcher:
    def __init__(self, app: QApplication) -> None:
        self._app = app
        self._settings = settings_store.load()
        self._index = Index()
        self._rebuild_index()

        self._search_bar = SearchBar(
            index=self._index,
            on_execute=self._on_execute,
            get_max_results=lambda: int(self._settings.get("max_results", 8)),
            get_hotkey=lambda: str(self._settings.get("hotkey", "Alt+Space")),
        )
        self._search_bar.setWindowIcon(make_app_icon())

        hotkey = str(self._settings.get("hotkey", "Alt+Space"))
        self._tray = Tray(
            on_show=self._show_bar,
            on_settings=self._open_settings,
            on_reload=self._rebuild_index,
            on_quit=self._quit,
            hotkey=hotkey,
        )
        self._tray.show()

        self._hotkey = HotkeyBridge(hotkey)
        self._hotkey.triggered.connect(self._toggle_bar, Qt.ConnectionType.QueuedConnection)
        self._hotkey.start_failed.connect(self._on_hotkey_error, Qt.ConnectionType.QueuedConnection)
        self._start_hotkey()
        self._apply_startup_setting()

    # -- index ----------------------------------------------------------------

    def _rebuild_index(self) -> None:
        self._index.rebuild(
            aliases=self._settings.get("aliases", {}),
            include_recent=bool(self._settings.get("include_recent_files", True)),
            include_apps=bool(self._settings.get("include_apps", True)),
            include_actions=bool(self._settings.get("include_quick_actions", True)),
        )

    # -- bar visibility -------------------------------------------------------

    def _show_bar(self) -> None:
        self._search_bar.show_centered()

    def _toggle_bar(self) -> None:
        if self._search_bar.isVisible():
            self._search_bar.dismiss()
        else:
            self._show_bar()

    # -- execution ------------------------------------------------------------

    def _on_execute(self, item: Item) -> None:
        try:
            if self._needs_confirmation(item) and not self._confirm_action(item):
                return
            execute_item(item, self._settings.get("aliases", {}))
        except Exception:  # noqa: BLE001
            QMessageBox.warning(
                None,
                "Utility Win",
                f"Failed to execute '{item.title}':\n\n{traceback.format_exc()}",
            )

    # -- settings -------------------------------------------------------------

    def _open_settings(self) -> None:
        old_hotkey = str(self._settings.get("hotkey", "Alt+Space"))
        dlg = SettingsDialog(self._settings)
        dlg.setWindowIcon(make_app_icon())
        if dlg.exec():
            self._settings = dlg.settings()
            settings_store.save(self._settings)
            self._apply_startup_setting()

            new_hotkey = str(self._settings.get("hotkey", "Alt+Space"))
            if new_hotkey != old_hotkey:
                self._restart_hotkey(new_hotkey)
            self._tray.set_hotkey_text(new_hotkey)
            self._rebuild_index()

    # -- settings effects -----------------------------------------------------

    def _start_hotkey(self) -> None:
        try:
            self._hotkey.start()
        except Exception as exc:  # noqa: BLE001
            QMessageBox.warning(None, "Utility Win", str(exc))

    def _restart_hotkey(self, hotkey: str) -> None:
        self._hotkey.stop()
        self._hotkey = HotkeyBridge(hotkey)
        self._hotkey.triggered.connect(self._toggle_bar, Qt.ConnectionType.QueuedConnection)
        self._hotkey.start_failed.connect(self._on_hotkey_error, Qt.ConnectionType.QueuedConnection)
        self._start_hotkey()

    def _on_hotkey_error(self, msg: str) -> None:
        QMessageBox.warning(None, "Utility Win", msg)

    def _apply_startup_setting(self) -> None:
        _set_launch_at_startup(bool(self._settings.get("launch_at_startup", False)))

    def _needs_confirmation(self, item: Item) -> bool:
        return (
            item.kind == "action"
            and item.payload in {"empty_recycle_bin", "shutdown", "restart", "signout"}
            and bool(self._settings.get("confirm_system_actions", True))
        )

    def _confirm_action(self, item: Item) -> bool:
        result = QMessageBox.question(
            None,
            "Confirm action",
            f"Run '{item.title}'?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        return result == QMessageBox.StandardButton.Yes

    # -- lifecycle ------------------------------------------------------------

    def _quit(self) -> None:
        self._hotkey.stop()
        self._tray.hide()
        self._app.quit()


def main() -> int:
    _set_app_user_model_id()
    if not _claim_single_instance():
        return 0

    app = QApplication(sys.argv)
    app.setApplicationName("Utility Win")
    app.setWindowIcon(make_app_icon())
    app.setQuitOnLastWindowClosed(False)

    if not _check_tray():
        QMessageBox.critical(None, "Utility Win", "System tray is unavailable on this system.")
        return 1

    launcher = Launcher(app)  # noqa: F841 - keeps refs alive
    return app.exec()


def _check_tray() -> bool:
    from PyQt6.QtWidgets import QSystemTrayIcon

    return QSystemTrayIcon.isSystemTrayAvailable()


def _set_launch_at_startup(enabled: bool) -> None:
    key_path = r"Software\Microsoft\Windows\CurrentVersion\Run"
    app_name = "Utility Win"
    command = f'"{sys.executable}" "{Path(__file__).resolve()}"'
    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path, 0, winreg.KEY_SET_VALUE) as key:
            if enabled:
                winreg.SetValueEx(key, app_name, 0, winreg.REG_SZ, command)
            else:
                try:
                    winreg.DeleteValue(key, app_name)
                except FileNotFoundError:
                    pass
    except OSError:
        pass


def _set_app_user_model_id() -> None:
    if sys.platform != "win32":
        return
    try:
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("UtilityWin.Launcher")
    except (AttributeError, OSError):
        pass


def _claim_single_instance() -> bool:
    global _mutex_handle
    if sys.platform != "win32":
        return True
    kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
    _mutex_handle = kernel32.CreateMutexW(None, False, "Local\\UtilityWinLauncherSingleInstance")
    if not _mutex_handle:
        return True
    return ctypes.get_last_error() != ERROR_ALREADY_EXISTS


if __name__ == "__main__":
    sys.exit(main())
