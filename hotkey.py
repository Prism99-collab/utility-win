"""Low-level Windows keyboard hotkey bridged to Qt."""
from __future__ import annotations

import ctypes
import sys
import threading

from PyQt6.QtCore import QObject, pyqtSignal


MOD_SHIFT = 0x0004
MOD_CONTROL = 0x0002
MOD_ALT = 0x0001
MOD_WIN = 0x0008

VK_SPACE = 0x20
VK_SHIFT = 0x10
VK_CONTROL = 0x11
VK_MENU = 0x12
VK_LSHIFT = 0xA0
VK_RSHIFT = 0xA1
VK_LCONTROL = 0xA2
VK_RCONTROL = 0xA3
VK_LMENU = 0xA4
VK_RMENU = 0xA5
VK_LWIN = 0x5B
VK_RWIN = 0x5C

WH_KEYBOARD_LL = 13
WM_KEYDOWN = 0x0100
WM_KEYUP = 0x0101
WM_SYSKEYDOWN = 0x0104
WM_SYSKEYUP = 0x0105
WM_QUIT = 0x0012


HOTKEY_CHOICES = [
    "Alt+Space",
    "Ctrl+Space",
    "Ctrl+Alt+Space",
    "Ctrl+Shift+Space",
    "Ctrl+Alt+K",
    "Ctrl+Shift+K",
    "Alt+Q",
    "Ctrl+Alt+L",
]

_MODIFIER_MAP = {
    "alt": MOD_ALT,
    "ctrl": MOD_CONTROL,
    "control": MOD_CONTROL,
    "shift": MOD_SHIFT,
    "win": MOD_WIN,
    "windows": MOD_WIN,
}

_KEY_MAP = {
    "space": VK_SPACE,
    "tab": 0x09,
    "enter": 0x0D,
    "return": 0x0D,
    "escape": 0x1B,
    "esc": 0x1B,
}

for _code in range(ord("A"), ord("Z") + 1):
    _KEY_MAP[chr(_code).lower()] = _code
for _code in range(ord("0"), ord("9") + 1):
    _KEY_MAP[chr(_code)] = _code
for _idx in range(1, 13):
    _KEY_MAP[f"f{_idx}"] = 0x70 + _idx - 1


if sys.platform == "win32":
    user32 = ctypes.WinDLL("user32", use_last_error=True)
    kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
else:
    user32 = None
    kernel32 = None


class KBDLLHOOKSTRUCT(ctypes.Structure):
    _fields_ = [
        ("vkCode", ctypes.c_ulong),
        ("scanCode", ctypes.c_ulong),
        ("flags", ctypes.c_ulong),
        ("time", ctypes.c_ulong),
        ("dwExtraInfo", ctypes.c_void_p),
    ]


class POINT(ctypes.Structure):
    _fields_ = [
        ("x", ctypes.c_long),
        ("y", ctypes.c_long),
    ]


class MSG(ctypes.Structure):
    _fields_ = [
        ("hwnd", ctypes.c_void_p),
        ("message", ctypes.c_uint),
        ("wParam", ctypes.c_size_t),
        ("lParam", ctypes.c_size_t),
        ("time", ctypes.c_ulong),
        ("pt", POINT),
    ]


LowLevelKeyboardProc = ctypes.WINFUNCTYPE(
    ctypes.c_long,
    ctypes.c_int,
    ctypes.c_size_t,
    ctypes.c_void_p,
)

if sys.platform == "win32":
    user32.SetWindowsHookExW.argtypes = [ctypes.c_int, LowLevelKeyboardProc, ctypes.c_void_p, ctypes.c_ulong]
    user32.SetWindowsHookExW.restype = ctypes.c_void_p
    user32.CallNextHookEx.argtypes = [ctypes.c_void_p, ctypes.c_int, ctypes.c_size_t, ctypes.c_void_p]
    user32.CallNextHookEx.restype = ctypes.c_long
    user32.UnhookWindowsHookEx.argtypes = [ctypes.c_void_p]
    user32.UnhookWindowsHookEx.restype = ctypes.c_bool


class HotkeyBridge(QObject):
    """Captures the configured hotkey before Windows or the foreground app uses it."""

    triggered = pyqtSignal()
    start_failed = pyqtSignal(str)

    def __init__(self, combo: str = "Alt+Space") -> None:
        super().__init__()
        self._combo = normalize_hotkey(combo)
        self._modifiers, self._key = parse_hotkey(self._combo)
        self._hook = None
        self._callback = None
        self._thread: threading.Thread | None = None
        self._thread_id = 0
        self._running = threading.Event()
        self._pressed_modifiers = 0
        self._armed = True

    def start(self) -> None:
        if sys.platform != "win32":
            raise RuntimeError("Global hotkey support is currently Windows-only.")
        if self._thread and self._thread.is_alive():
            return
        self._running.set()
        self._thread = threading.Thread(target=self._run_hook, name="UtilityWinHotkey", daemon=True)
        self._thread.start()

    def stop(self) -> None:
        self._running.clear()
        if self._thread_id:
            user32.PostThreadMessageW(self._thread_id, WM_QUIT, 0, 0)
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=1.0)
        self._thread = None
        self._thread_id = 0

    def _run_hook(self) -> None:
        self._thread_id = kernel32.GetCurrentThreadId()
        self._callback = LowLevelKeyboardProc(self._handle_key)
        self._hook = user32.SetWindowsHookExW(WH_KEYBOARD_LL, self._callback, None, 0)
        if not self._hook:
            err = ctypes.get_last_error()
            self._running.clear()
            self.start_failed.emit(f"Could not install keyboard hook for '{self._combo}'. Win32 error: {err}")
            return

        msg = MSG()
        try:
            while self._running.is_set() and user32.GetMessageW(ctypes.byref(msg), None, 0, 0) > 0:
                user32.TranslateMessage(ctypes.byref(msg))
                user32.DispatchMessageW(ctypes.byref(msg))
        finally:
            if self._hook:
                user32.UnhookWindowsHookEx(self._hook)
                self._hook = None

    def _handle_key(self, n_code: int, w_param: int, l_param: int) -> int:
        if n_code < 0:
            return user32.CallNextHookEx(self._hook, n_code, w_param, l_param)

        event = ctypes.cast(l_param, ctypes.POINTER(KBDLLHOOKSTRUCT)).contents
        vk = int(event.vkCode)
        is_down = w_param in (WM_KEYDOWN, WM_SYSKEYDOWN)
        is_up = w_param in (WM_KEYUP, WM_SYSKEYUP)

        if vk in _MODIFIER_VKS:
            bit = _MODIFIER_VKS[vk]
            if is_down:
                self._pressed_modifiers |= bit
            elif is_up:
                self._pressed_modifiers &= ~bit

        if vk == self._key:
            if is_down and self._matches():
                if self._armed:
                    self._armed = False
                    self.triggered.emit()
                return 1
            if is_up and not self._armed:
                self._armed = True
                return 1

        return user32.CallNextHookEx(self._hook, n_code, w_param, l_param)

    def _matches(self) -> bool:
        return self._pressed_modifiers & self._modifiers == self._modifiers


_MODIFIER_VKS = {
    VK_SHIFT: MOD_SHIFT,
    VK_LSHIFT: MOD_SHIFT,
    VK_RSHIFT: MOD_SHIFT,
    VK_CONTROL: MOD_CONTROL,
    VK_LCONTROL: MOD_CONTROL,
    VK_RCONTROL: MOD_CONTROL,
    VK_MENU: MOD_ALT,
    VK_LMENU: MOD_ALT,
    VK_RMENU: MOD_ALT,
    VK_LWIN: MOD_WIN,
    VK_RWIN: MOD_WIN,
}


def normalize_hotkey(combo: str) -> str:
    parts = [p.strip() for p in combo.replace("<", "").replace(">", "").split("+") if p.strip()]
    if not parts:
        return "Alt+Space"

    modifiers: list[str] = []
    key = parts[-1]
    for part in parts[:-1]:
        lowered = part.lower()
        if lowered in ("ctrl", "control"):
            label = "Ctrl"
        elif lowered == "alt":
            label = "Alt"
        elif lowered == "shift":
            label = "Shift"
        elif lowered in ("win", "windows"):
            label = "Win"
        else:
            continue
        if label not in modifiers:
            modifiers.append(label)

    key_label = _format_key(key)
    if not modifiers:
        modifiers = ["Alt"]
    return "+".join(modifiers + [key_label])


def parse_hotkey(combo: str) -> tuple[int, int]:
    parts = [p.strip().lower() for p in normalize_hotkey(combo).split("+") if p.strip()]
    modifiers = 0
    key = 0
    for part in parts:
        if part in _MODIFIER_MAP:
            modifiers |= _MODIFIER_MAP[part]
        elif part in _KEY_MAP:
            key = _KEY_MAP[part]
    if not modifiers or not key:
        raise ValueError(f"Invalid hotkey: {combo}")
    return modifiers, key


def _format_key(key: str) -> str:
    lowered = key.strip().lower()
    if lowered == "space":
        return "Space"
    if lowered in ("esc", "escape"):
        return "Esc"
    if lowered in ("enter", "return"):
        return "Enter"
    if len(lowered) == 1:
        return lowered.upper()
    if lowered.startswith("f") and lowered[1:].isdigit():
        return lowered.upper()
    return key.strip().title()
