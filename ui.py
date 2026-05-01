"""Premium command launcher UI and settings dialog."""
from __future__ import annotations

import ctypes
import sys
from ctypes import wintypes
from pathlib import Path
from typing import Any, Callable

from PyQt6.QtCore import (
    QFileInfo,
    QEasingCurve,
    QEvent,
    QPropertyAnimation,
    QRect,
    QSize,
    QTimer,
    Qt,
)
from PyQt6.QtGui import (
    QColor,
    QCursor,
    QFont,
    QGuiApplication,
    QIcon,
    QImage,
    QKeyEvent,
    QPainter,
    QPainterPath,
    QPen,
    QPixmap,
)
from PyQt6.QtWidgets import (
    QApplication,
    QCheckBox,
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QFileIconProvider,
    QSizePolicy,
    QSpinBox,
    QStyle,
    QStyledItemDelegate,
    QStyleOptionViewItem,
    QTabWidget,
    QTableWidget,
    QTableWidgetItem,
    QToolButton,
    QVBoxLayout,
    QWidget,
)

from app_icon import make_app_icon
from hotkey import HOTKEY_CHOICES, normalize_hotkey
from indexer import Index, Item


_QSS = """
QWidget#searchBar {
    background: transparent;
    border: none;
}
QFrame#searchRow {
    background-color: rgba(17, 19, 29, 253);
    border: none;
    border-bottom: 1px solid rgba(255, 255, 255, 16);
    border-top-left-radius: 18px;
    border-top-right-radius: 18px;
}
QLabel#appMark {
    background: transparent;
    padding-left: 26px;
    padding-right: 20px;
    border-right: 1px solid rgba(255, 255, 255, 14);
}
QLabel#searchGlyph {
    color: #b8c4de;
    background: transparent;
    padding-left: 26px;
    padding-right: 22px;
    border-right: 1px solid rgba(255, 255, 255, 14);
    font-size: 24px;
}
QLineEdit#query {
    background: transparent;
    border: none;
    color: #e8eaf2;
    padding: 18px 22px 26px 20px;
    font-size: 26px;
    font-weight: 400;
    selection-background-color: rgba(91, 141, 238, 140);
}
QLabel#hotkeyChip {
    color: #b8c8dc;
    background-color: rgba(255, 255, 255, 12);
    border: 1px solid rgba(255, 255, 255, 34);
    border-radius: 6px;
    padding: 5px 14px;
    margin-right: 22px;
    font-size: 12px;
    font-weight: 600;
}
QLineEdit#query:focus {
    outline: none;
}
QFrame#suggestionsPanel {
    background-color: rgba(12, 13, 21, 246);
    border: none;
}
QLabel#suggestionsTitle {
    color: #5a6880;
    background: transparent;
    font-size: 10px;
    font-weight: 700;
    padding: 4px 0 10px 0;
}
QToolButton#suggestionTile {
    background-color: rgba(255, 255, 255, 6);
    border: 1px solid rgba(255, 255, 255, 20);
    border-radius: 12px;
    color: #c8d0e4;
    padding: 9px 14px;
    font-size: 13px;
    font-weight: 500;
    text-align: left;
}
QToolButton#suggestionTile:hover {
    background-color: rgba(91, 141, 238, 26);
    border: 1px solid rgba(110, 158, 255, 70);
    color: #e8eaf2;
}
QToolButton#suggestionTile:pressed {
    background-color: rgba(91, 141, 238, 44);
}
QToolButton#suggestionTile:selected {
    background-color: rgba(91, 141, 238, 30);
    border: 1px solid rgba(91, 141, 238, 80);
}
QListWidget#results {
    background: rgba(12, 13, 21, 246);
    border: none;
    outline: 0;
    padding: 6px 0 4px 0;
}
QListWidget#results::item {
    border: none;
}
QFrame#footer {
    background-color: rgba(14, 15, 24, 252);
    border: none;
    border-top: 1px solid rgba(255, 255, 255, 12);
    border-bottom-left-radius: 18px;
    border-bottom-right-radius: 18px;
}
QLabel#hint {
    color: #6a7488;
    background: transparent;
    padding: 8px 16px;
    font-size: 11px;
}
QLabel#keycap {
    color: #d8dff0;
    background-color: rgba(255, 255, 255, 14);
    border: 1px solid rgba(255, 255, 255, 38);
    border-radius: 6px;
    padding: 5px 10px;
    font-size: 12px;
    font-weight: 600;
}
QLabel#keyHint {
    color: #68788e;
    background: transparent;
    padding-right: 22px;
    font-size: 12px;
}
QFrame#metaRow {
    background-color: rgba(12, 13, 21, 246);
    border: none;
}
QLabel#metaLabel {
    color: #5a6880;
    background: transparent;
    padding: 8px 16px 2px 16px;
    font-size: 10px;
    font-weight: 700;
}
QFrame#noResults {
    background-color: rgba(12, 13, 21, 246);
    border: none;
}
QLabel#noResultsTitle {
    color: #e1e7f5;
    background: transparent;
    font-size: 15px;
    font-weight: 700;
}
QLabel#noResultsSubtitle {
    color: #6f819c;
    background: transparent;
    font-size: 12px;
}
QDialog#settings {
    background-color: #0f1018;
    color: #e8eaf2;
}
QDialog#settings QLabel {
    color: #c0cade;
}
QLabel#settingsTitle {
    color: #e8eaf2;
    font-size: 19px;
    font-weight: 700;
}
QLabel#settingsSubtitle {
    color: #5a6880;
    font-size: 12px;
}
QTabWidget::pane {
    background-color: #11131d;
    border: 1px solid rgba(255, 255, 255, 14);
    border-radius: 10px;
    top: -1px;
}
QTabBar::tab {
    background-color: transparent;
    color: #6f819c;
    padding: 9px 16px;
    margin-right: 4px;
    border-top-left-radius: 8px;
    border-top-right-radius: 8px;
    font-weight: 600;
}
QTabBar::tab:selected {
    color: #e8eaf2;
    background-color: #171a28;
    border: 1px solid rgba(255, 255, 255, 14);
    border-bottom-color: #171a28;
}
QTabBar::tab:hover:!selected {
    color: #b8c8dc;
    background-color: rgba(255, 255, 255, 5);
}
QTableWidget {
    background-color: #141521;
    color: #e8eaf2;
    gridline-color: rgba(255, 255, 255, 12);
    border: 1px solid rgba(255, 255, 255, 18);
    border-radius: 9px;
    selection-background-color: rgba(91, 141, 238, 130);
}
QHeaderView::section {
    background-color: #1c1e2e;
    color: #c0cade;
    border: 0;
    padding: 8px 10px;
    font-weight: 600;
}
QLineEdit, QSpinBox {
    background-color: #141521;
    color: #e8eaf2;
    border: 1px solid rgba(255, 255, 255, 18);
    border-radius: 8px;
    padding: 7px 9px;
}
QComboBox {
    background-color: #141521;
    color: #e8eaf2;
    border: 1px solid rgba(255, 255, 255, 18);
    border-radius: 8px;
    padding: 7px 28px 7px 9px;
    min-height: 28px;
}
QComboBox:hover, QLineEdit:hover, QSpinBox:hover {
    border: 1px solid rgba(255, 255, 255, 30);
}
QComboBox::drop-down {
    border: none;
    width: 24px;
}
QComboBox QAbstractItemView {
    background-color: #141521;
    color: #e8eaf2;
    border: 1px solid rgba(255, 255, 255, 18);
    selection-background-color: rgba(91, 141, 238, 120);
    outline: 0;
}
QCheckBox {
    color: #c0cade;
    spacing: 10px;
}
QCheckBox::indicator {
    width: 16px;
    height: 16px;
    border-radius: 4px;
    border: 1px solid rgba(255, 255, 255, 28);
    background-color: #141521;
}
QCheckBox::indicator:checked {
    background-color: #5b8dee;
    border: 1px solid rgba(120, 170, 255, 180);
}
QPushButton {
    background-color: #1e2032;
    color: #e8eaf2;
    border: 1px solid rgba(255, 255, 255, 18);
    border-radius: 8px;
    padding: 7px 14px;
    min-height: 28px;
}
QPushButton:hover {
    background-color: #272a3e;
    border: 1px solid rgba(255, 255, 255, 28);
}
QPushButton:pressed {
    background-color: #31354f;
}
QDialogButtonBox QPushButton {
    min-width: 86px;
}
"""


_CATEGORY_STYLE: dict[str, tuple[str, QColor, str]] = {
    "app": ("▶", QColor(91, 141, 238), "APP"),
    "action": ("⚡", QColor(220, 158, 78), "ACTION"),
    "alias": ("★", QColor(152, 105, 210), "ALIAS"),
    "folder": ("▣", QColor(200, 160, 60), "FOLDER"),
    "excel": ("X", QColor(68, 168, 102), "EXCEL"),
    "word": ("W", QColor(78, 138, 234), "WORD"),
    "ppt": ("P", QColor(214, 107, 72), "PPT"),
    "pdf": ("P", QColor(208, 72, 72), "PDF"),
    "text": ("≡", QColor(140, 150, 168), "TEXT"),
    "image": ("◧", QColor(208, 106, 158), "IMAGE"),
    "video": ("▶", QColor(198, 86, 122), "VIDEO"),
    "audio": ("♪", QColor(72, 182, 182), "AUDIO"),
    "archive": ("▦", QColor(170, 122, 75), "ZIP"),
    "code": ("<>", QColor(86, 192, 136), "CODE"),
    "data": ("DB", QColor(98, 178, 166), "DATA"),
    "power": ("⏻", QColor(220, 82, 82), "POWER"),
    "file": ("•", QColor(122, 132, 150), "FILE"),
    "recent": ("◷", QColor(70, 172, 150), "RECENT"),
}
_DEFAULT_CATEGORY_STYLE = ("•", QColor(122, 132, 150), "ITEM")
_HEADER_ROLE = "section-header"


def _is_header_data(data: object) -> bool:
    return isinstance(data, dict) and data.get("role") == _HEADER_ROLE


def _section_for_item(item: Item) -> str:
    if item.kind == "alias":
        return "Aliases"
    if item.kind == "action":
        return "Actions"
    if item.kind == "app":
        return "Apps"
    if item.kind == "recent":
        if item.category == "folder":
            return "Recent Folders"
        return "Recent Files"
    return "Results"


def _apply_win11_chrome(hwnd: int) -> None:
    if sys.platform != "win32":
        return
    try:
        dwm = ctypes.windll.dwmapi
    except (AttributeError, OSError):
        return

    border = ctypes.c_uint32(0xFFFFFFFE)
    corner = ctypes.c_int(2)
    for attr, value in ((34, border), (33, corner)):
        try:
            dwm.DwmSetWindowAttribute(
                hwnd, attr, ctypes.byref(value), ctypes.sizeof(value)
            )
        except OSError:
            continue


def _force_foreground(hwnd: int) -> None:
    if sys.platform != "win32":
        return
    try:
        user32 = ctypes.windll.user32
        current_thread = ctypes.windll.kernel32.GetCurrentThreadId()
        foreground = user32.GetForegroundWindow()
        foreground_thread = user32.GetWindowThreadProcessId(foreground, None) if foreground else 0

        if foreground_thread and foreground_thread != current_thread:
            user32.AttachThreadInput(foreground_thread, current_thread, True)

        user32.AllowSetForegroundWindow(0xFFFFFFFF)
        user32.ShowWindow(hwnd, 5)
        user32.BringWindowToTop(hwnd)
        user32.SetForegroundWindow(hwnd)
        user32.SetActiveWindow(hwnd)
        user32.SetFocus(hwnd)

        if foreground_thread and foreground_thread != current_thread:
            user32.AttachThreadInput(foreground_thread, current_thread, False)
    except (AttributeError, OSError):
        return


def _foreground_window() -> int:
    if sys.platform != "win32":
        return 0
    try:
        return int(ctypes.windll.user32.GetForegroundWindow())
    except (AttributeError, OSError):
        return 0


def _restore_foreground(hwnd: int) -> None:
    if sys.platform != "win32" or not hwnd:
        return
    try:
        user32 = ctypes.windll.user32
        if not user32.IsWindow(hwnd):
            return
        current_thread = ctypes.windll.kernel32.GetCurrentThreadId()
        target_thread = user32.GetWindowThreadProcessId(hwnd, None)
        if target_thread and target_thread != current_thread:
            user32.AttachThreadInput(target_thread, current_thread, True)
        user32.AllowSetForegroundWindow(0xFFFFFFFF)
        user32.BringWindowToTop(hwnd)
        user32.SetForegroundWindow(hwnd)
        if target_thread and target_thread != current_thread:
            user32.AttachThreadInput(target_thread, current_thread, False)
    except (AttributeError, OSError):
        return


def _release_hotkey_modifiers() -> None:
    if sys.platform != "win32":
        return
    try:
        user32 = ctypes.windll.user32
        key_up = 0x0002
        for vk in (0x12, 0xA4, 0xA5, 0x11, 0xA2, 0xA3, 0x10, 0xA0, 0xA1):
            user32.keybd_event(vk, 0, key_up, 0)
    except (AttributeError, OSError):
        return


class _SHFILEINFO(ctypes.Structure):
    _fields_ = [
        ("hIcon", wintypes.HICON),
        ("iIcon", ctypes.c_int),
        ("dwAttributes", wintypes.DWORD),
        ("szDisplayName", wintypes.WCHAR * 260),
        ("szTypeName", wintypes.WCHAR * 80),
    ]


class _BITMAPINFOHEADER(ctypes.Structure):
    _fields_ = [
        ("biSize", wintypes.DWORD),
        ("biWidth", wintypes.LONG),
        ("biHeight", wintypes.LONG),
        ("biPlanes", wintypes.WORD),
        ("biBitCount", wintypes.WORD),
        ("biCompression", wintypes.DWORD),
        ("biSizeImage", wintypes.DWORD),
        ("biXPelsPerMeter", wintypes.LONG),
        ("biYPelsPerMeter", wintypes.LONG),
        ("biClrUsed", wintypes.DWORD),
        ("biClrImportant", wintypes.DWORD),
    ]


class _BITMAPINFO(ctypes.Structure):
    _fields_ = [
        ("bmiHeader", _BITMAPINFOHEADER),
        ("bmiColors", wintypes.DWORD * 3),
    ]


def _shell_icon_for_path(path: str, size: int = 32) -> QIcon:
    if sys.platform != "win32" or not path:
        return QIcon()
    try:
        shell32 = ctypes.windll.shell32
        user32 = ctypes.windll.user32
        gdi32 = ctypes.windll.gdi32

        shfi = _SHFILEINFO()
        flags = 0x000000100 | 0x000000000
        shell32.SHGetFileInfoW(
            str(path),
            0,
            ctypes.byref(shfi),
            ctypes.sizeof(shfi),
            flags,
        )
        if not shfi.hIcon:
            return QIcon()

        hdc = user32.GetDC(None)
        mem_dc = gdi32.CreateCompatibleDC(hdc)
        bits = ctypes.c_void_p()
        bmi = _BITMAPINFO()
        bmi.bmiHeader.biSize = ctypes.sizeof(_BITMAPINFOHEADER)
        bmi.bmiHeader.biWidth = size
        bmi.bmiHeader.biHeight = -size
        bmi.bmiHeader.biPlanes = 1
        bmi.bmiHeader.biBitCount = 32
        bmi.bmiHeader.biCompression = 0
        bitmap = gdi32.CreateDIBSection(
            mem_dc, ctypes.byref(bmi), 0, ctypes.byref(bits), None, 0
        )
        old = gdi32.SelectObject(mem_dc, bitmap)
        ctypes.memset(bits, 0, size * size * 4)
        user32.DrawIconEx(mem_dc, 0, 0, shfi.hIcon, size, size, 0, None, 0x0003)
        image_bytes = ctypes.string_at(bits, size * size * 4)
        image = QImage(image_bytes, size, size, QImage.Format.Format_ARGB32).copy()
        gdi32.SelectObject(mem_dc, old)
        gdi32.DeleteObject(bitmap)
        gdi32.DeleteDC(mem_dc)
        user32.ReleaseDC(None, hdc)
        user32.DestroyIcon(shfi.hIcon)
        return QIcon(QPixmap.fromImage(image))
    except (AttributeError, OSError, ValueError):
        return QIcon()


class ResultDelegate(QStyledItemDelegate):
    ROW_H = 58
    HEADER_H = 26
    PAD_X = 12
    BADGE = 40
    GAP = 14

    def sizeHint(self, option: QStyleOptionViewItem, index) -> QSize:  # noqa: N802
        if _is_header_data(index.data(Qt.ItemDataRole.UserRole)):
            return QSize(0, self.HEADER_H)
        return QSize(0, self.ROW_H)

    def paint(self, painter: QPainter, option: QStyleOptionViewItem, index) -> None:  # noqa: N802
        data = index.data(Qt.ItemDataRole.UserRole)
        if _is_header_data(data):
            painter.save()
            painter.setRenderHint(QPainter.RenderHint.TextAntialiasing, True)
            painter.setFont(QFont("Segoe UI Variable", 8, QFont.Weight.DemiBold))
            painter.setPen(QColor(88, 102, 124))
            painter.drawText(
                option.rect.adjusted(26, 4, -18, 0),
                Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft,
                str(data.get("title", "")).upper(),
            )
            painter.restore()
            return

        item: Item = data
        if item is None:
            return

        painter.save()
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        painter.setRenderHint(QPainter.RenderHint.TextAntialiasing, True)

        rect = option.rect
        selected = bool(option.state & QStyle.StateFlag.State_Selected)
        hovered = bool(option.state & QStyle.StateFlag.State_MouseOver)
        bg_rect = rect.adjusted(self.PAD_X, 4, -self.PAD_X, -4)

        painter.setPen(Qt.PenStyle.NoPen)
        if selected:
            painter.setBrush(QColor(34, 49, 86))
            painter.drawRoundedRect(bg_rect, 11, 11)
            painter.setBrush(QColor(91, 141, 238, 16))
            painter.drawRoundedRect(bg_rect.adjusted(1, 1, -1, -1), 10, 10)
            painter.setPen(QPen(QColor(116, 162, 255, 58), 1))
            painter.drawRoundedRect(bg_rect.adjusted(0, 0, -1, -1), 11, 11)
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QColor(91, 141, 238))
            painter.drawRoundedRect(QRect(bg_rect.x(), bg_rect.y() + 10, 3, bg_rect.height() - 20), 2, 2)
        elif hovered:
            painter.setBrush(QColor(255, 255, 255, 9))
            painter.drawRoundedRect(bg_rect, 11, 11)

        category = item.category or item.kind
        glyph, accent, chip_text = _CATEGORY_STYLE.get(category, _DEFAULT_CATEGORY_STYLE)
        badge_rect = QRect(
            bg_rect.x() + 12,
            bg_rect.y() + (bg_rect.height() - self.BADGE) // 2,
            self.BADGE,
            self.BADGE,
        )
        tint = QColor(accent)
        tint.setAlpha(38 if selected else 22)
        border = QColor(accent)
        border.setAlpha(120 if selected else 88)
        painter.setBrush(tint)
        painter.setPen(QPen(border, 1))
        painter.drawRoundedRect(badge_rect, 11, 11)
        icon: QIcon | None = index.data(Qt.ItemDataRole.DecorationRole)
        if isinstance(icon, QIcon) and not icon.isNull():
            icon_rect = badge_rect.adjusted(8, 8, -8, -8)
            icon.paint(painter, icon_rect, Qt.AlignmentFlag.AlignCenter)
        else:
            painter.setPen(accent.lighter(125))
            painter.setFont(QFont("Segoe UI", 12, QFont.Weight.DemiBold))
            painter.drawText(badge_rect, Qt.AlignmentFlag.AlignCenter, glyph)

        chip_font = QFont("Segoe UI", 7, QFont.Weight.DemiBold)
        painter.setFont(chip_font)
        chip_w = painter.fontMetrics().horizontalAdvance(chip_text) + 16
        chip_rect = QRect(
            bg_rect.right() - chip_w - 10,
            bg_rect.y() + (bg_rect.height() - 19) // 2,
            chip_w,
            19,
        )

        text_x = badge_rect.right() + self.GAP
        text_w = max(40, chip_rect.left() - text_x - 12)

        painter.setFont(QFont("Segoe UI Variable", 10, QFont.Weight.DemiBold))
        painter.setPen(QColor(242, 244, 252) if selected else QColor(224, 226, 236))
        painter.drawText(
            QRect(text_x, bg_rect.y() + 9, text_w, 22),
            Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft,
            _elide(painter, item.title, text_w),
        )

        painter.setFont(QFont("Segoe UI Variable", 8))
        painter.setPen(QColor(188, 196, 212) if selected else QColor(122, 134, 156))
        painter.drawText(
            QRect(text_x, bg_rect.y() + 32, text_w, 18),
            Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft,
            _elide(painter, item.subtitle, text_w),
        )

        painter.setPen(Qt.PenStyle.NoPen)
        chip_bg = QColor(accent) if selected else QColor(255, 255, 255)
        chip_bg.setAlpha(34 if selected else 8)
        painter.setBrush(chip_bg)
        painter.drawRoundedRect(chip_rect, 6, 6)
        painter.setPen(accent.lighter(150) if selected else QColor(140, 154, 176))
        painter.setFont(chip_font)
        painter.drawText(chip_rect, Qt.AlignmentFlag.AlignCenter, chip_text)
        painter.restore()


def _elide(painter: QPainter, text: str, width: int) -> str:
    return painter.fontMetrics().elidedText(text, Qt.TextElideMode.ElideRight, max(0, width))


def _tile_title(title: str) -> str:
    replacements = {
        "Codex Account Switcher": "Codex",
        "Open Downloads": "Downloads",
        "Open Documents": "Documents",
        "Open Desktop": "Desktop",
    }
    return replacements.get(title, title)


def _file_explorer_icon() -> QIcon:
    icon = QIcon()
    for size in (24, 32, 48, 64):
        pix = QPixmap(size, size)
        pix.fill(Qt.GlobalColor.transparent)
        painter = QPainter(pix)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)

        scale = size / 48
        outer = QRect(round(5 * scale), round(8 * scale), round(38 * scale), round(30 * scale))
        painter.setPen(QPen(QColor(206, 218, 238), max(1, round(1.2 * scale))))
        painter.setBrush(QColor(245, 248, 252))
        painter.drawRoundedRect(outer, 3 * scale, 3 * scale)

        header = QRect(outer.x() + 1, outer.y() + 1, outer.width() - 2, round(7 * scale))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QColor(221, 229, 240))
        painter.drawRoundedRect(header, 2 * scale, 2 * scale)

        nav = QRect(outer.x() + round(4 * scale), outer.y() + round(11 * scale), round(10 * scale), round(21 * scale))
        painter.setBrush(QColor(234, 239, 246))
        painter.drawRoundedRect(nav, 2 * scale, 2 * scale)

        pane = QRect(outer.x() + round(17 * scale), outer.y() + round(11 * scale), round(16 * scale), round(19 * scale))
        painter.setBrush(QColor(61, 151, 223))
        painter.drawRoundedRect(pane, 2 * scale, 2 * scale)

        painter.setPen(QPen(QColor(132, 148, 171), max(1, round(scale))))
        for y in (15, 20, 25):
            yy = outer.y() + round(y * scale)
            painter.drawLine(outer.x() + round(36 * scale), yy, outer.x() + round(39 * scale), yy)
        painter.end()
        icon.addPixmap(pix)
    return icon


class SearchBar(QWidget):
    def __init__(
        self,
        index: Index,
        on_execute: Callable[[Item], None],
        get_max_results: Callable[[], int],
        get_hotkey: Callable[[], str] | None = None,
    ) -> None:
        super().__init__()
        self._index = index
        self._on_execute = on_execute
        self._get_max_results = get_max_results
        self._get_hotkey = get_hotkey or (lambda: "Alt+Space")
        self._previous_hwnd = 0
        self._dismissing = False
        self._icon_provider = QFileIconProvider()
        self._icon_cache: dict[tuple[str, str], QIcon] = {}
        self._last_render_signature: tuple[str, tuple[tuple[str, str, str], ...]] | None = None
        self._suggestion_buttons: list[QToolButton] = []
        self._current_suggestions: list[Item] = []
        self._refresh_timer = QTimer(self)
        self._refresh_timer.setSingleShot(True)
        self._refresh_timer.setInterval(12)
        self._refresh_timer.timeout.connect(self._refresh_results_now)

        self.setObjectName("searchBar")
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.Window
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setAutoFillBackground(False)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.setStyleSheet(_QSS)

        self._fade = QPropertyAnimation(self, b"windowOpacity")
        self._fade.setDuration(110)
        self._fade.setEasingCurve(QEasingCurve.Type.OutCubic)

        self._build_ui()

    def _build_ui(self) -> None:
        QApplication.instance().setFont(QFont("Segoe UI Variable", 10))

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        search_row = QFrame(self)
        search_row.setObjectName("searchRow")
        search_layout = QHBoxLayout(search_row)
        search_layout.setContentsMargins(0, 0, 0, 0)
        search_layout.setSpacing(0)

        app_mark = QLabel(search_row)
        app_mark.setObjectName("appMark")
        app_mark.setPixmap(make_app_icon().pixmap(34, 34))
        search_layout.addWidget(app_mark)

        glyph = QLabel("⌕", search_row)
        glyph.setObjectName("searchGlyph")
        search_layout.addWidget(glyph)

        self._query = QLineEdit(search_row)
        self._query.setObjectName("query")
        self._query.setPlaceholderText("Search apps, actions, files, aliases...")
        self._query.installEventFilter(self)
        self._query.textChanged.connect(self._schedule_refresh_results)
        self._query.returnPressed.connect(self._exec_selected)
        search_layout.addWidget(self._query, 1)

        self._hotkey_chip = QLabel(self._format_hotkey(self._get_hotkey()), search_row)
        self._hotkey_chip.setObjectName("hotkeyChip")
        self._hotkey_chip.setFixedHeight(48)
        self._hotkey_chip.setMinimumWidth(116)
        self._hotkey_chip.setAlignment(Qt.AlignmentFlag.AlignCenter)
        search_layout.addWidget(self._hotkey_chip)
        root.addWidget(search_row)

        self._suggestions_panel = QFrame(self)
        self._suggestions_panel.setObjectName("suggestionsPanel")
        suggestions_layout = QVBoxLayout(self._suggestions_panel)
        suggestions_layout.setContentsMargins(30, 20, 30, 22)
        suggestions_layout.setSpacing(8)
        suggestions_title = QLabel("SUGGESTED", self._suggestions_panel)
        suggestions_title.setObjectName("suggestionsTitle")
        suggestions_layout.addWidget(suggestions_title)
        self._suggestions_grid = QGridLayout()
        self._suggestions_grid.setHorizontalSpacing(12)
        self._suggestions_grid.setVerticalSpacing(14)
        for col in range(4):
            self._suggestions_grid.setColumnStretch(col, 1)
        suggestions_layout.addLayout(self._suggestions_grid)
        root.addWidget(self._suggestions_panel)

        meta_row = QFrame(self)
        meta_row.setObjectName("metaRow")
        meta_layout = QHBoxLayout(meta_row)
        meta_layout.setContentsMargins(0, 0, 0, 0)
        self._meta = QLabel("SUGGESTIONS", meta_row)
        self._meta.setObjectName("metaLabel")
        meta_layout.addWidget(self._meta)
        meta_layout.addStretch(1)
        root.addWidget(meta_row)
        self._meta_row = meta_row

        self._list = QListWidget(self)
        self._list.setObjectName("results")
        self._list.setMouseTracking(True)
        self._list.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self._list.installEventFilter(self)
        self._list.setUniformItemSizes(False)
        self._list.setFrameShape(QFrame.Shape.NoFrame)
        self._list.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self._list.setItemDelegate(ResultDelegate(self._list))
        self._list.setVerticalScrollMode(QListWidget.ScrollMode.ScrollPerPixel)
        self._list.itemActivated.connect(lambda _i: self._exec_selected())
        self._list.itemClicked.connect(lambda _i: self._exec_selected())
        root.addWidget(self._list)

        self._no_results = QFrame(self)
        self._no_results.setObjectName("noResults")
        no_results_layout = QVBoxLayout(self._no_results)
        no_results_layout.setContentsMargins(34, 22, 34, 24)
        no_results_layout.setSpacing(5)
        no_results_title = QLabel("No matches", self._no_results)
        no_results_title.setObjectName("noResultsTitle")
        no_results_subtitle = QLabel(
            "Try another app name, file type, folder, or alias.",
            self._no_results,
        )
        no_results_subtitle.setObjectName("noResultsSubtitle")
        no_results_layout.addWidget(no_results_title)
        no_results_layout.addWidget(no_results_subtitle)
        no_results_layout.addStretch(1)
        self._no_results.setVisible(False)
        root.addWidget(self._no_results)

        self._footer = QFrame(self)
        self._footer.setObjectName("footer")
        footer_layout = QHBoxLayout(self._footer)
        footer_layout.setContentsMargins(34, 22, 34, 22)
        footer_layout.setSpacing(10)
        for key, label in (("Enter", "Open"), ("↑↓", "Navigate"), ("Esc", "Close")):
            keycap = QLabel(key, self._footer)
            keycap.setObjectName("keycap")
            footer_layout.addWidget(keycap)
            text = QLabel(label, self._footer)
            text.setObjectName("keyHint")
            footer_layout.addWidget(text)
        footer_layout.addStretch(1)
        brand = QLabel("Utility Win", self._footer)
        brand.setObjectName("hint")
        footer_layout.addWidget(brand)
        root.addWidget(self._footer)

        self.setFixedWidth(856)

    def paintEvent(self, event) -> None:  # noqa: N802
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_Clear)
        painter.fillRect(self.rect(), Qt.GlobalColor.transparent)
        painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_SourceOver)

        panel = self.rect().adjusted(0, 0, -1, -1)

        path = QPainterPath()
        path.addRoundedRect(panel.toRectF(), 18, 18)
        painter.fillPath(path, QColor(12, 13, 21, 250))
        painter.setPen(QPen(QColor(210, 222, 245, 24), 1))
        painter.drawPath(path)

        for inset, alpha in ((1, 10), (2, 6), (3, 3)):
            inner_path = QPainterPath()
            inner_path.addRoundedRect(
                QRect(panel).adjusted(inset, inset, -inset, -inset).toRectF(),
                18 - inset,
                18 - inset,
            )
            painter.setPen(QPen(QColor(255, 255, 255, alpha), 1))
            painter.drawPath(inner_path)
        super().paintEvent(event)

    def show_centered(self) -> None:
        self._previous_hwnd = _foreground_window()
        self._query.clear()
        self._last_render_signature = None
        self._refresh_timer.stop()
        self._refresh_results_now()
        self._center_on_active_screen()
        self.setWindowOpacity(0.0)
        self.show()
        self.raise_()
        self.activateWindow()
        self._focus_query()
        QTimer.singleShot(0, self._focus_query)
        QTimer.singleShot(35, self._focus_query)
        QTimer.singleShot(90, self._focus_query)

        self._fade.stop()
        self._fade.setStartValue(0.0)
        self._fade.setEndValue(1.0)
        self._fade.start()

    def dismiss(self, *, restore_focus: bool = True) -> None:
        if self._dismissing:
            return
        self._dismissing = True
        self.releaseKeyboard()
        self._query.releaseKeyboard()
        self._query.clearFocus()
        self.hide()
        _release_hotkey_modifiers()
        if restore_focus and self._previous_hwnd and self._previous_hwnd != int(self.winId()):
            QTimer.singleShot(0, lambda hwnd=self._previous_hwnd: _restore_foreground(hwnd))
            QTimer.singleShot(80, lambda hwnd=self._previous_hwnd: _restore_foreground(hwnd))
        self._dismissing = False

    def hideEvent(self, event) -> None:  # noqa: N802
        self.releaseKeyboard()
        self._query.releaseKeyboard()
        self._query.clearFocus()
        _release_hotkey_modifiers()
        super().hideEvent(event)

    def _focus_query(self) -> None:
        if not self.isVisible():
            return
        _force_foreground(int(self.winId()))
        self.raise_()
        self.activateWindow()
        self._query.setFocus(Qt.FocusReason.ShortcutFocusReason)
        self._query.activateWindow()

    def _center_on_active_screen(self) -> None:
        screen = QGuiApplication.screenAt(QCursor.pos()) or QGuiApplication.primaryScreen()
        geo = screen.availableGeometry()
        self.adjustSize()
        x = geo.x() + (geo.width() - self.width()) // 2
        y = geo.y() + int(geo.height() * 0.22)
        self.move(x, y)

    def _schedule_refresh_results(self) -> None:
        self._refresh_timer.start()

    def _refresh_results_now(self) -> None:
        query = self._query.text()
        limit = self._get_max_results()
        results = self._index.search(query, limit=limit)
        signature = (
            query,
            tuple((it.kind, it.payload, it.title) for it in results),
        )
        if signature == self._last_render_signature:
            return
        self._last_render_signature = signature

        if not query.strip():
            self._render_suggestions(results)
            self._suggestions_panel.setVisible(True)
            self._meta_row.setVisible(False)
            self._list.setVisible(False)
            self._no_results.setVisible(False)
            self._list.setFixedHeight(0)
            self.adjustSize()
            return

        self._suggestions_panel.setVisible(False)
        self._meta_row.setVisible(True)
        self._no_results.setVisible(not results)
        self._list.setVisible(bool(results))
        self._list.clear()
        self._meta.setText(f"{len(results)} MATCHES" if results else "NO RESULTS")
        grouped_results = self._group_results(results)
        last_section = ""
        total_h = 14 if results else 0
        self._list.setUpdatesEnabled(False)
        for it in grouped_results:
            section = _section_for_item(it)
            if section != last_section:
                header = QListWidgetItem()
                header.setData(Qt.ItemDataRole.UserRole, {"role": _HEADER_ROLE, "title": section})
                header.setFlags(Qt.ItemFlag.NoItemFlags)
                header.setSizeHint(QSize(0, ResultDelegate.HEADER_H))
                self._list.addItem(header)
                total_h += ResultDelegate.HEADER_H
                last_section = section

            entry = QListWidgetItem()
            entry.setData(Qt.ItemDataRole.UserRole, it)
            entry.setData(Qt.ItemDataRole.DecorationRole, self._icon_for_item(it))
            entry.setSizeHint(QSize(0, ResultDelegate.ROW_H))
            self._list.addItem(entry)
            total_h += ResultDelegate.ROW_H
        self._select_first_result()
        self._list.setUpdatesEnabled(True)

        self._list.setFixedHeight(total_h if results else 0)
        self._no_results.setFixedHeight(112 if not results else 0)
        self.adjustSize()

    def _render_suggestions(self, suggestions: list[Item]) -> None:
        self._current_suggestions = suggestions[:8]
        for btn in self._suggestion_buttons:
            self._suggestions_grid.removeWidget(btn)
            btn.deleteLater()
        self._suggestion_buttons = []

        for idx, item in enumerate(self._current_suggestions):
            btn = QToolButton(self._suggestions_panel)
            btn.setObjectName("suggestionTile")
            btn.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextBesideIcon)
            btn.setIcon(self._icon_for_item(item))
            btn.setIconSize(QSize(28, 28))
            btn.setText(_tile_title(item.title))
            btn.setToolTip(f"{item.title}\n{item.subtitle}")
            btn.setFixedHeight(62)
            btn.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
            btn.clicked.connect(lambda _checked=False, payload=item: self._execute_payload(payload))
            self._suggestions_grid.addWidget(btn, idx // 4, idx % 4)
            self._suggestion_buttons.append(btn)

    def _group_results(self, results: list[Item]) -> list[Item]:
        order = ["Aliases", "Actions", "Apps", "Recent Folders", "Recent Files", "Results"]
        buckets: dict[str, list[Item]] = {name: [] for name in order}
        for item in results:
            section = _section_for_item(item)
            buckets.setdefault(section, []).append(item)
        grouped: list[Item] = []
        for section in order:
            grouped.extend(buckets.get(section, []))
        return grouped

    def _exec_selected(self) -> None:
        if self._suggestions_panel.isVisible() and self._current_suggestions:
            self._execute_payload(self._current_suggestions[0])
            return
        item = self._list.currentItem()
        if item is None:
            return
        payload: Item = item.data(Qt.ItemDataRole.UserRole)
        if _is_header_data(payload):
            self._move_selection(1)
            return
        self._execute_payload(payload)

    def _execute_payload(self, payload: Item) -> None:
        self.dismiss(restore_focus=False)
        self._on_execute(payload)

    def _icon_for_item(self, item: Item) -> QIcon:
        cache_key = (item.kind, item.payload or item.category)
        cached = self._icon_cache.get(cache_key)
        if cached is not None:
            return cached

        icon = QIcon()
        if item.kind == "action" and item.payload == "open_file_explorer":
            icon = _file_explorer_icon()
            self._icon_cache[cache_key] = icon
            return icon
        if item.kind == "action" and item.payload == "open_this_pc":
            icon = self.style().standardIcon(QStyle.StandardPixmap.SP_ComputerIcon)
            self._icon_cache[cache_key] = icon
            return icon
        if item.kind == "action" and item.payload in {"open_downloads", "open_documents", "open_desktop"}:
            folder = {
                "open_downloads": Path.home() / "Downloads",
                "open_documents": Path.home() / "Documents",
                "open_desktop": Path.home() / "Desktop",
            }[item.payload]
            icon = _shell_icon_for_path(str(folder))
            if icon.isNull():
                icon = self._icon_provider.icon(QFileInfo(str(folder)))
            if not icon.isNull():
                self._icon_cache[cache_key] = icon
                return icon
        if item.kind in ("app", "recent") and item.payload:
            icon = _shell_icon_for_path(item.payload)
            if icon.isNull():
                icon = self._icon_provider.icon(QFileInfo(item.payload))
            if not icon.isNull():
                self._icon_cache[cache_key] = icon
                return icon
        if item.category == "folder":
            icon = self.style().standardIcon(QStyle.StandardPixmap.SP_DirIcon)
        elif item.kind == "action":
            icon = self.style().standardIcon(QStyle.StandardPixmap.SP_CommandLink)
        elif item.kind == "alias":
            icon = self.style().standardIcon(QStyle.StandardPixmap.SP_FileDialogDetailedView)
        else:
            icon = self.style().standardIcon(QStyle.StandardPixmap.SP_FileIcon)
        self._icon_cache[cache_key] = icon
        return icon

    def _select_first_result(self) -> None:
        for row in range(self._list.count()):
            if not _is_header_data(self._list.item(row).data(Qt.ItemDataRole.UserRole)):
                self._list.setCurrentRow(row)
                return
        self._list.setCurrentRow(-1)

    def _move_selection(self, delta: int) -> None:
        if self._suggestions_panel.isVisible():
            return
        if self._list.count() == 0:
            return
        row = self._list.currentRow()
        if row < 0:
            self._select_first_result()
            return
        next_row = row + delta
        while 0 <= next_row < self._list.count():
            data = self._list.item(next_row).data(Qt.ItemDataRole.UserRole)
            if not _is_header_data(data):
                self._list.setCurrentRow(next_row)
                return
            next_row += delta

    def _format_hotkey(self, hotkey: str) -> str:
        return hotkey.replace("+", " ")

    def keyPressEvent(self, event: QKeyEvent) -> None:  # noqa: N802
        key = event.key()
        if key == Qt.Key.Key_Escape:
            self.dismiss()
            return
        if key == Qt.Key.Key_Down:
            self._move_selection(1)
            return
        if key == Qt.Key.Key_Up:
            self._move_selection(-1)
            return
        if event.text() and not event.modifiers() & (
            Qt.KeyboardModifier.ControlModifier | Qt.KeyboardModifier.AltModifier
        ):
            self._query.insert(event.text())
            return
        self._query.setFocus(Qt.FocusReason.ShortcutFocusReason)
        super().keyPressEvent(event)

    def eventFilter(self, watched, event) -> bool:  # noqa: N802
        if event.type() == QEvent.Type.KeyPress:
            key = event.key()
            if key == Qt.Key.Key_Escape:
                self.dismiss()
                return True
            if key == Qt.Key.Key_Down:
                self._move_selection(1)
                return True
            if key == Qt.Key.Key_Up:
                self._move_selection(-1)
                return True
        return super().eventFilter(watched, event)

    def changeEvent(self, event) -> None:  # noqa: N802
        if event.type() == QEvent.Type.ActivationChange:
            if self.isVisible() and not self.isActiveWindow():
                self.dismiss(restore_focus=False)
        super().changeEvent(event)

    def showEvent(self, event) -> None:  # noqa: N802
        super().showEvent(event)
        _apply_win11_chrome(int(self.winId()))


class SettingsDialog(QDialog):
    def __init__(self, settings: dict[str, Any], parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("settings")
        self.setWindowTitle("Utility Win - Settings")
        self.resize(760, 560)
        self.setStyleSheet(_QSS)
        self._result: dict[str, Any] = dict(settings)
        aliases = dict(settings.get("aliases", {}))

        layout = QVBoxLayout(self)
        layout.setContentsMargins(22, 22, 22, 22)
        layout.setSpacing(14)

        title = QLabel("Utility Win Settings")
        title.setObjectName("settingsTitle")
        layout.addWidget(title)

        sub = QLabel("Control launch behavior, search sources, safety prompts, and custom commands.")
        sub.setObjectName("settingsSubtitle")
        layout.addWidget(sub)

        tabs = QTabWidget(self)
        tabs.addTab(self._general_tab(settings), "General")
        tabs.addTab(self._search_tab(settings), "Search")
        tabs.addTab(self._aliases_tab(aliases), "Aliases")
        layout.addWidget(tabs, 1)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self._accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def _general_tab(self, settings: dict[str, Any]) -> QWidget:
        tab = QWidget(self)
        layout = QGridLayout(tab)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setHorizontalSpacing(16)
        layout.setVerticalSpacing(14)

        self._hotkey = QComboBox(tab)
        self._hotkey.addItems(HOTKEY_CHOICES)
        current_hotkey = normalize_hotkey(str(settings.get("hotkey", "Alt+Space")))
        if current_hotkey not in HOTKEY_CHOICES:
            self._hotkey.addItem(current_hotkey)
        self._hotkey.setCurrentText(current_hotkey)

        self._launch_at_startup = QCheckBox("Start Utility Win when I sign in", tab)
        self._launch_at_startup.setChecked(bool(settings.get("launch_at_startup", False)))

        self._confirm_system_actions = QCheckBox("Confirm shutdown, restart, sign out, and recycle-bin actions", tab)
        self._confirm_system_actions.setChecked(bool(settings.get("confirm_system_actions", True)))

        layout.addWidget(QLabel("Global hotkey"), 0, 0)
        layout.addWidget(self._hotkey, 0, 1)
        layout.addWidget(self._launch_at_startup, 1, 0, 1, 2)
        layout.addWidget(self._confirm_system_actions, 2, 0, 1, 2)
        layout.setColumnStretch(1, 1)
        layout.setRowStretch(3, 1)
        return tab

    def _search_tab(self, settings: dict[str, Any]) -> QWidget:
        tab = QWidget(self)
        layout = QGridLayout(tab)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setHorizontalSpacing(16)
        layout.setVerticalSpacing(14)

        self._include_apps = QCheckBox("Start Menu apps", tab)
        self._include_apps.setChecked(bool(settings.get("include_apps", True)))
        self._include_actions = QCheckBox("Quick system actions", tab)
        self._include_actions.setChecked(bool(settings.get("include_quick_actions", True)))
        self._include_recent = QCheckBox("Recent files", tab)
        self._include_recent.setChecked(bool(settings.get("include_recent_files", True)))
        self._full_file_scan = QCheckBox("Full user-folder scan for more accurate file search", tab)
        self._full_file_scan.setChecked(bool(settings.get("full_file_scan", False)))
        self._full_file_scan.setToolTip(
            "Scans your whole user profile instead of only common folders. Slower on large PCs."
        )

        self._max_results = QSpinBox(tab)
        self._max_results.setRange(4, 12)
        self._max_results.setValue(int(settings.get("max_results", 8)))

        layout.addWidget(QLabel("Search sources"), 0, 0)
        layout.addWidget(self._include_apps, 0, 1)
        layout.addWidget(self._include_actions, 1, 1)
        layout.addWidget(self._include_recent, 2, 1)
        layout.addWidget(self._full_file_scan, 3, 1)
        layout.addWidget(QLabel("Maximum results"), 4, 0)
        layout.addWidget(self._max_results, 4, 1)
        layout.setColumnStretch(1, 1)
        layout.setRowStretch(5, 1)
        return tab

    def _aliases_tab(self, aliases: dict[str, str]) -> QWidget:
        tab = QWidget(self)
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        self._table = QTableWidget(0, 2, tab)
        self._table.setHorizontalHeaderLabels(["Alias", "Command"])
        self._table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        self._table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self._table.verticalHeader().setVisible(False)
        self._table.setAlternatingRowColors(False)
        layout.addWidget(self._table, 1)

        for name, cmd in aliases.items():
            self._add_row(name, cmd)

        btn_row = QHBoxLayout()
        add_btn = QPushButton("+ Add alias")
        remove_btn = QPushButton("Remove selected")
        add_btn.clicked.connect(lambda: self._add_row("", ""))
        remove_btn.clicked.connect(self._remove_selected)
        btn_row.addWidget(add_btn)
        btn_row.addWidget(remove_btn)
        btn_row.addStretch(1)
        layout.addLayout(btn_row)
        return tab

    def _add_row(self, name: str, cmd: str) -> None:
        row = self._table.rowCount()
        self._table.insertRow(row)
        self._table.setItem(row, 0, QTableWidgetItem(name))
        self._table.setItem(row, 1, QTableWidgetItem(cmd))

    def _remove_selected(self) -> None:
        for idx in sorted({i.row() for i in self._table.selectedIndexes()}, reverse=True):
            self._table.removeRow(idx)

    def _accept(self) -> None:
        aliases: dict[str, str] = {}
        for row in range(self._table.rowCount()):
            name_item = self._table.item(row, 0)
            cmd_item = self._table.item(row, 1)
            name = (name_item.text() if name_item else "").strip()
            cmd = (cmd_item.text() if cmd_item else "").strip()
            if name and cmd:
                aliases[name] = cmd

        self._result["aliases"] = aliases
        self._result["hotkey"] = normalize_hotkey(self._hotkey.currentText())
        self._result["launch_at_startup"] = self._launch_at_startup.isChecked()
        self._result["include_apps"] = self._include_apps.isChecked()
        self._result["include_quick_actions"] = self._include_actions.isChecked()
        self._result["include_recent_files"] = self._include_recent.isChecked()
        self._result["full_file_scan"] = self._full_file_scan.isChecked()
        self._result["confirm_system_actions"] = self._confirm_system_actions.isChecked()
        self._result["max_results"] = self._max_results.value()
        self.accept()

    def settings(self) -> dict[str, Any]:
        return self._result

    def aliases(self) -> dict[str, str]:
        return dict(self._result.get("aliases", {}))
