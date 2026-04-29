"""System tray icon with menu: Show, Settings, Reload Index, Quit."""
from __future__ import annotations

from typing import Callable

from PyQt6.QtGui import QAction
from PyQt6.QtWidgets import QMenu, QSystemTrayIcon

from app_icon import make_app_icon


class Tray(QSystemTrayIcon):
    def __init__(
        self,
        *,
        on_show: Callable[[], None],
        on_settings: Callable[[], None],
        on_reload: Callable[[], None],
        on_quit: Callable[[], None],
        hotkey: str,
    ) -> None:
        super().__init__(make_app_icon())
        self.set_hotkey_text(hotkey)

        menu = QMenu()
        a_show = QAction("Show launcher", menu)
        a_show.triggered.connect(on_show)
        a_settings = QAction("Settings...", menu)
        a_settings.triggered.connect(on_settings)
        a_reload = QAction("Reload index", menu)
        a_reload.triggered.connect(on_reload)
        a_quit = QAction("Quit", menu)
        a_quit.triggered.connect(on_quit)

        menu.addAction(a_show)
        menu.addAction(a_settings)
        menu.addAction(a_reload)
        menu.addSeparator()
        menu.addAction(a_quit)
        self.setContextMenu(menu)

        self.activated.connect(
            lambda reason: on_show()
            if reason == QSystemTrayIcon.ActivationReason.Trigger
            else None
        )

    def set_hotkey_text(self, hotkey: str) -> None:
        self.setToolTip(f"Utility Win ({hotkey})")
