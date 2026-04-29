"""Builds and searches the launcher index."""
from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Literal

ItemKind = Literal["app", "action", "recent", "alias"]


@dataclass(frozen=True)
class Item:
    title: str
    subtitle: str
    kind: ItemKind
    payload: str
    category: str = ""


QUICK_ACTIONS: list[Item] = [
    Item("This PC", "Computer and drives", "action", "open_this_pc", "folder"),
    Item("File Explorer", "Windows file manager", "action", "open_file_explorer", "app"),
    Item("Empty Recycle Bin", "System cleanup", "action", "empty_recycle_bin", "action"),
    Item("Toggle Dark Mode", "Windows appearance", "action", "toggle_dark_mode", "action"),
    Item("Lock Screen", "Security action", "action", "lock", "action"),
    Item("Open Desktop", "Desktop folder", "action", "open_desktop", "folder"),
    Item("Open Downloads", "Downloads folder", "action", "open_downloads", "folder"),
    Item("Open Documents", "Documents folder", "action", "open_documents", "folder"),
    Item("Shutdown", "Power action", "action", "shutdown", "power"),
    Item("Restart", "Power action", "action", "restart", "power"),
    Item("Sign Out", "Account action", "action", "signout", "power"),
]


_EXT_MAP: dict[str, tuple[str, str]] = {
    ".exe": ("app", "Application"),
    ".msi": ("app", "Installer"),
    ".appref-ms": ("app", "Application"),
    ".xlsx": ("excel", "Excel spreadsheet"),
    ".xls": ("excel", "Excel spreadsheet"),
    ".xlsm": ("excel", "Excel spreadsheet"),
    ".xlsb": ("excel", "Excel spreadsheet"),
    ".ods": ("excel", "Spreadsheet"),
    ".csv": ("excel", "CSV spreadsheet"),
    ".docx": ("word", "Word document"),
    ".doc": ("word", "Word document"),
    ".dotx": ("word", "Word template"),
    ".odt": ("word", "Document"),
    ".rtf": ("word", "Rich-text document"),
    ".one": ("word", "OneNote notebook"),
    ".pptx": ("ppt", "PowerPoint presentation"),
    ".ppt": ("ppt", "PowerPoint presentation"),
    ".ppsx": ("ppt", "PowerPoint slideshow"),
    ".odp": ("ppt", "Presentation"),
    ".pdf": ("pdf", "PDF document"),
    ".txt": ("text", "Text file"),
    ".md": ("text", "Markdown file"),
    ".log": ("text", "Log file"),
    ".jpg": ("image", "Image"),
    ".jpeg": ("image", "Image"),
    ".png": ("image", "Image"),
    ".gif": ("image", "Image"),
    ".bmp": ("image", "Image"),
    ".webp": ("image", "Image"),
    ".svg": ("image", "Vector image"),
    ".ico": ("image", "Icon"),
    ".psd": ("image", "Photoshop document"),
    ".ai": ("image", "Illustrator document"),
    ".fig": ("image", "Figma design"),
    ".xd": ("image", "Adobe XD design"),
    ".mp4": ("video", "Video"),
    ".mkv": ("video", "Video"),
    ".mov": ("video", "Video"),
    ".avi": ("video", "Video"),
    ".webm": ("video", "Video"),
    ".mp3": ("audio", "Audio"),
    ".wav": ("audio", "Audio"),
    ".flac": ("audio", "Audio"),
    ".m4a": ("audio", "Audio"),
    ".ogg": ("audio", "Audio"),
    ".zip": ("archive", "Archive"),
    ".7z": ("archive", "Archive"),
    ".rar": ("archive", "Archive"),
    ".tar": ("archive", "Archive"),
    ".gz": ("archive", "Archive"),
    ".iso": ("archive", "Disk image"),
    ".py": ("code", "Python source"),
    ".js": ("code", "JavaScript source"),
    ".ts": ("code", "TypeScript source"),
    ".tsx": ("code", "TypeScript source"),
    ".jsx": ("code", "JavaScript source"),
    ".cpp": ("code", "C++ source"),
    ".c": ("code", "C source"),
    ".h": ("code", "C header"),
    ".hpp": ("code", "C++ header"),
    ".cs": ("code", "C# source"),
    ".java": ("code", "Java source"),
    ".go": ("code", "Go source"),
    ".rs": ("code", "Rust source"),
    ".rb": ("code", "Ruby source"),
    ".php": ("code", "PHP source"),
    ".html": ("code", "HTML"),
    ".css": ("code", "CSS"),
    ".json": ("code", "JSON"),
    ".jsonl": ("code", "JSON Lines"),
    ".xml": ("code", "XML"),
    ".yml": ("code", "YAML"),
    ".yaml": ("code", "YAML"),
    ".toml": ("code", "TOML"),
    ".sh": ("code", "Shell script"),
    ".bat": ("code", "Batch script"),
    ".cmd": ("code", "Batch script"),
    ".ps1": ("code", "PowerShell script"),
    ".sln": ("code", "Visual Studio solution"),
    ".csproj": ("code", "C# project"),
    ".vcxproj": ("code", "C++ project"),
    ".db": ("data", "Database"),
    ".sqlite": ("data", "SQLite database"),
    ".sqlite3": ("data", "SQLite database"),
}

_RECENT_ALLOWED_EXTENSIONS = {
    ".docx", ".doc", ".dotx", ".odt", ".rtf", ".one",
    ".xlsx", ".xls", ".xlsm", ".xlsb", ".ods", ".csv",
    ".pptx", ".ppt", ".ppsx", ".odp",
    ".pdf", ".txt", ".md",
    ".jpg", ".jpeg", ".png", ".gif", ".bmp", ".webp", ".svg", ".ico",
    ".mp4", ".mkv", ".mov", ".avi", ".webm",
    ".mp3", ".wav", ".flac", ".m4a", ".ogg",
    ".zip", ".7z", ".rar", ".iso",
}

_RECENT_BLOCKED_EXTENSIONS = {
    ".tmp", ".temp", ".bak", ".old", ".crdownload", ".part", ".lnk",
    ".dll", ".sys", ".drv", ".mui", ".dat", ".cab", ".msi", ".exe",
    ".ini", ".inf", ".log", ".etl", ".pf", ".manifest",
}

_RECENT_BLOCKED_WORDS = {
    "appdata", "programdata", "windows", "system32", "syswow64", "$recycle.bin",
    "node_modules", "__pycache__", ".git", "cache", "temp", "tmp", "crash",
    "diagnostic", "telemetry", "package cache",
}

_APP_BLOCKED_PHRASES = {
    "windows defender firewall with advanced security",
    "odbc data sources",
    "component services",
    "computer management",
    "event viewer",
    "iscsi initiator",
    "local security policy",
    "performance monitor",
    "print management",
    "resource monitor",
    "services",
    "system configuration",
    "system information",
    "task scheduler",
    "windows memory diagnostic",
    "windows powershell (x86)",
}


def _start_menu_dirs() -> list[Path]:
    candidates = [
        Path(os.environ.get("ProgramData", r"C:\ProgramData")) / "Microsoft" / "Windows" / "Start Menu" / "Programs",
        Path(os.environ.get("APPDATA", "")) / "Microsoft" / "Windows" / "Start Menu" / "Programs",
        Path.home() / "Desktop",
        Path(os.environ.get("PUBLIC", r"C:\Users\Public")) / "Desktop",
    ]
    return [p for p in candidates if p.exists()]


def _user_search_roots() -> list[Path]:
    home = Path.home()
    candidates = [
        home / "Desktop",
        home / "Downloads",
        home / "Documents",
        home / "Pictures",
        home / "Videos",
        home / "Music",
    ]
    return [p for p in candidates if p.exists()]


def _classify_name(name: str) -> tuple[str, str]:
    ext = Path(name).suffix.lower()
    if ext in _EXT_MAP:
        return _EXT_MAP[ext]
    if ext:
        return "file", f"{ext.lstrip('.').upper()} file"
    return "folder", "Folder"


def _classify_path(path_text: str, fallback_name: str) -> tuple[str, str, str]:
    path = Path(path_text) if path_text else Path(fallback_name)
    name = path.name or fallback_name
    if path_text and _is_folder(path):
        return name or str(path), "folder", _folder_subtitle(path)

    category, subtitle = _classify_name(name)
    title = path.stem if path.suffix else name
    return title or fallback_name, category, _path_subtitle(path, subtitle)


def _is_folder(path: Path) -> bool:
    try:
        return path.exists() and path.is_dir()
    except OSError:
        return not path.suffix


def _path_subtitle(path: Path, default: str) -> str:
    home = Path.home()
    known = [
        (home / "Desktop", "Desktop item"),
        (home / "Downloads", "Downloaded file"),
        (home / "Pictures", "Image"),
        (home / "Videos", "Video"),
        (home / "Music", "Audio"),
    ]
    resolved = _safe_resolve(path)
    for root, label in known:
        if _contains(root, resolved):
            return label
    return default


def _folder_subtitle(path: Path) -> str:
    home = Path.home()
    known = [
        (home / "Desktop", "Desktop folder"),
        (home / "Downloads", "Downloads folder"),
        (home / "Documents", "Documents folder"),
        (home / "Pictures", "Pictures folder"),
        (home / "Videos", "Videos folder"),
        (home / "Music", "Music folder"),
    ]
    resolved = _safe_resolve(path)
    for root, label in known:
        if _contains(root, resolved):
            return label
    return "Folder"


def _safe_resolve(path: Path) -> Path:
    try:
        return path.resolve()
    except OSError:
        return path


def _contains(root: Path, path: Path) -> bool:
    try:
        return root.exists() and path.is_relative_to(root.resolve())
    except OSError:
        return False


def _scan_apps() -> list[Item]:
    seen: dict[str, Item] = {}
    for root in _start_menu_dirs():
        for lnk in root.rglob("*.lnk"):
            name = lnk.stem
            if _skip_app_shortcut(name):
                continue
            key = name.lower()
            if key in seen:
                continue
            seen[key] = Item(name, _app_subtitle(name, ""), "app", str(lnk), "app")
    return sorted(seen.values(), key=lambda i: i.title.lower())


def _skip_app_shortcut(name: str) -> bool:
    lowered = name.lower().strip()
    return lowered in _APP_BLOCKED_PHRASES


def _scan_recent(limit: int = 120) -> list[Item]:
    recent_dir = Path(os.environ.get("APPDATA", "")) / "Microsoft" / "Windows" / "Recent"
    if not recent_dir.exists():
        return []

    candidates: list[tuple[float, Path]] = []
    for lnk in recent_dir.glob("*.lnk"):
        try:
            candidates.append((lnk.stat().st_mtime, lnk))
        except OSError:
            continue
    candidates.sort(key=lambda e: e[0], reverse=True)
    candidates = candidates[:limit]
    entries: list[tuple[float, Item]] = []
    for mtime, lnk in candidates:
        fallback = lnk.stem
        if _skip_recent_shortcut(fallback):
            continue
        title, category, subtitle = _classify_path("", fallback)
        if category == "file" and Path(fallback).suffix:
            continue
        entries.append((mtime, Item(title, subtitle, "recent", str(lnk), category)))

    entries.sort(key=lambda e: e[0], reverse=True)
    return [item for _, item in entries[:limit]]


def _scan_user_files(limit: int = 900, max_depth: int = 5) -> list[Item]:
    items: list[Item] = []
    seen_paths: set[str] = set()

    for root in _user_search_roots():
        stack: list[tuple[Path, int]] = [(root, 0)]
        while stack and len(items) < limit:
            current, depth = stack.pop()
            try:
                entries = sorted(current.iterdir(), key=lambda p: (not p.is_dir(), p.name.lower()))
            except OSError:
                continue

            for path in entries:
                if len(items) >= limit:
                    break
                if _skip_user_path(path):
                    continue
                key = str(_safe_resolve(path)).lower()
                if key in seen_paths:
                    continue
                seen_paths.add(key)

                if path.is_dir():
                    title, category, subtitle = _classify_path(str(path), path.name)
                    items.append(Item(title, subtitle, "recent", str(path), category))
                    if depth < max_depth:
                        stack.append((path, depth + 1))
                    continue

                suffix = path.suffix.lower()
                if suffix not in _RECENT_ALLOWED_EXTENSIONS:
                    continue
                title, category, subtitle = _classify_path(str(path), path.name)
                items.append(Item(title, subtitle, "recent", str(path), category))

    return items


def _skip_user_path(path: Path) -> bool:
    name = path.name
    lowered = name.lower()
    if lowered.startswith(("~$", ".")) or lowered in {"desktop.ini", "thumbs.db"}:
        return True
    if any(word in lowered for word in _RECENT_BLOCKED_WORDS):
        return True
    try:
        if path.is_file() and path.suffix.lower() in _RECENT_BLOCKED_EXTENSIONS:
            return True
    except OSError:
        return True
    return False


def _skip_recent_shortcut(name: str) -> bool:
    lowered = name.lower()
    if any(word in lowered for word in _RECENT_BLOCKED_WORDS):
        return True

    suffix = Path(name).suffix.lower()
    if suffix in _RECENT_BLOCKED_EXTENSIONS:
        return True
    if suffix and suffix not in _RECENT_ALLOWED_EXTENSIONS:
        return True

    noisy_prefixes = ("~$", ".", "desktop.ini", "thumbs.db")
    return lowered.startswith(noisy_prefixes)


def _alias_items(aliases: dict[str, str]) -> list[Item]:
    return [
        Item(title=name, subtitle="Custom command", kind="alias", payload=name, category="alias")
        for name in aliases
    ]


def _app_subtitle(name: str, target: str) -> str:
    text = f"{name} {target}".lower()
    hints = [
        (("chrome", "edge", "firefox", "browser", "brave", "opera"), "Web browser"),
        (("discord",), "Communication app"),
        (("code.exe", "visual studio code", "devenv", "pycharm", "cursor"), "Code editor"),
        (("codex",), "Codex utility"),
        (("claude",), "AI assistant"),
        (("powershell", "cmd.exe", "terminal", "wt.exe"), "Terminal"),
        (("word", "winword"), "Word processor"),
        (("excel",), "Spreadsheet app"),
        (("powerpnt", "powerpoint"), "Presentation app"),
        (("photoshop", "illustrator", "figma", "xd"), "Design app"),
        (("steam", "epic games", "riot client", "battle.net"), "Game launcher"),
        (("settings", "control panel"), "System utility"),
    ]
    for needles, label in hints:
        if any(needle in text for needle in needles):
            return label
    return "Application"


class Index:
    def __init__(self) -> None:
        self._apps: list[Item] = []
        self._recent: list[Item] = []
        self._aliases: list[Item] = []
        self._include_recent = True
        self._include_apps = True
        self._include_actions = True
        self._items: list[Item] = []
        self._empty_items: list[Item] = []
        self._suggestions: list[Item] = []

    def rebuild(
        self,
        *,
        aliases: dict[str, str],
        include_recent: bool,
        include_apps: bool = True,
        include_actions: bool = True,
    ) -> None:
        self._apps = _scan_apps() if include_apps else []
        self._recent = _merge_user_items(_scan_user_files(), _scan_recent()) if include_recent else []
        self._aliases = _alias_items(aliases)
        self._include_recent = include_recent
        self._include_apps = include_apps
        self._include_actions = include_actions
        self._items = list(self._aliases)
        if self._include_actions:
            self._items.extend(QUICK_ACTIONS)
        if self._include_apps:
            self._items.extend(self._apps)
        if self._include_recent:
            self._items.extend(self._recent)

        self._suggestions = _build_suggestions(
            aliases=self._aliases,
            actions=QUICK_ACTIONS if self._include_actions else [],
            apps=self._apps if self._include_apps else [],
            recent=self._recent if self._include_recent else [],
        )
        self._empty_items = self._suggestions

    def all_items(self) -> Iterable[Item]:
        yield from self._items

    def search(self, query: str, limit: int = 8) -> list[Item]:
        q = query.strip().lower()
        if not q:
            return self._empty_items[:limit]

        scored: list[tuple[float, int, Item]] = []
        for order, item in enumerate(self._items):
            score = _item_score(q, item)
            if score > 0:
                score += _kind_bonus(item)
                scored.append((score, order, item))
        scored.sort(key=lambda s: (-s[0], _kind_rank(s[2]), s[2].title.lower()))
        return [item for _, _, item in scored[:limit]]


def _merge_user_items(*groups: list[Item]) -> list[Item]:
    merged: list[Item] = []
    seen: set[tuple[str, str]] = set()
    for group in groups:
        for item in group:
            key = (item.title.lower(), item.category)
            if key in seen:
                continue
            seen.add(key)
            merged.append(item)
    return merged


def _kind_bonus(item: Item) -> float:
    if item.kind == "alias":
        return 25
    if item.kind == "app":
        return 12
    if item.kind == "action":
        return 8
    return 0


def _kind_rank(item: Item) -> int:
    return {"alias": 0, "app": 1, "action": 2, "recent": 3}.get(item.kind, 9)


def _item_score(query: str, item: Item) -> float:
    title = item.title.lower()
    subtitle = item.subtitle.lower()
    category = item.category.lower()
    category_aliases = {
        "excel": {"xls", "xlsx", "xlsm", "csv", "spreadsheet"},
        "word": {"doc", "docx", "document"},
        "ppt": {"ppt", "pptx", "powerpoint", "presentation"},
        "pdf": {"pdf"},
        "image": {"jpg", "jpeg", "png", "photo", "image"},
        "video": {"mp4", "mov", "mkv", "video"},
        "audio": {"mp3", "wav", "audio", "music"},
        "archive": {"zip", "rar", "7z"},
        "folder": {"dir", "directory", "folder"},
    }
    score = _fuzzy_score(query, title)
    if query == category:
        score = max(score, 440.0)
    elif query in category_aliases.get(category, set()):
        score = max(score, 420.0)
    elif category.startswith(query):
        score = max(score, 260.0)
    if query in subtitle:
        score = max(score, 210.0)
    return score


def _build_suggestions(
    *,
    aliases: list[Item],
    actions: list[Item],
    apps: list[Item],
    recent: list[Item],
) -> list[Item]:
    suggestions: list[Item] = []
    seen: set[tuple[str, str]] = set()

    def add(item: Item | None) -> None:
        if item is None:
            return
        key = (item.kind, item.payload.lower())
        if key in seen:
            return
        seen.add(key)
        suggestions.append(item)

    action_by_payload = {item.payload: item for item in actions}
    for payload in ("open_this_pc", "open_file_explorer"):
        add(action_by_payload.get(payload))

    app_preferences = [
        ("brave",),
        ("discord",),
        ("codex",),
        ("claude",),
        ("chatgpt",),
        ("cursor",),
        ("visual studio code", "vscode", "code"),
        ("chrome",),
    ]
    for names in app_preferences:
        add(_find_app(apps, names))

    for payload in ("open_downloads", "open_documents", "open_desktop"):
        add(action_by_payload.get(payload))

    for item in aliases[:2]:
        add(item)
    for item in recent:
        if item.category == "folder":
            add(item)
        if len(suggestions) >= 12:
            break
    return suggestions


def _find_app(apps: list[Item], names: tuple[str, ...]) -> Item | None:
    for app in apps:
        title = app.title.lower()
        if any(title == name or name in title for name in names):
            return app
    return None


def _fuzzy_score(query: str, target: str) -> float:
    if not query:
        return 0.0
    if query == target:
        return 1000.0
    if target.startswith(query):
        return 500.0 - len(target) * 0.1
    if query in target:
        idx = target.find(query)
        boundary = idx == 0 or not target[idx - 1].isalnum()
        return (300.0 if boundary else 200.0) - len(target) * 0.1
    if len(query) <= 3:
        return 0.0

    qi = 0
    last_match = -1
    score = 0.0
    for ti, ch in enumerate(target):
        if qi < len(query) and ch == query[qi]:
            if last_match == ti - 1:
                score += 5.0
            elif ti == 0 or not target[ti - 1].isalnum():
                score += 3.0
            else:
                score += 1.0
            last_match = ti
            qi += 1
    if qi < len(query):
        return 0.0
    return score - len(target) * 0.05
