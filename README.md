# Utility Win

Utility Win is a premium Spotlight-style launcher for Windows. It lives in the system tray and opens instantly with a global hotkey so you can launch apps, folders, files, aliases, and quick system actions without leaving the keyboard.

## Features

- Fast global hotkey launcher, defaulting to `Alt+Space`.
- Focused search input on open, with clean dismissal back to the previous window.
- Fuzzy search across Start Menu apps, quick actions, aliases, recent items, and common user folders.
- Optional full user-folder scan for users who want broader file search coverage.
- Smarter category detection for folders, PDFs, Word, Excel, PowerPoint, images, videos, audio, archives, code, and data files.
- Real Windows shell icons for apps and files where possible.
- Settings for hotkey, startup, search sources, max results, aliases, and safety confirmations.
- Single-instance tray app with Show, Settings, Reload index, and Quit.

## Install

Use the MSI from the latest GitHub release. It installs `UtilityWin.exe` and creates a desktop shortcut named **Utility Win**.

## Run From Source

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python main.py
```

The app starts in the system tray. Use the tray menu or the configured hotkey to open the launcher.

## Build The MSI

```powershell
pip install -r requirements.txt
pip install -r requirements-dev.txt
python setup.py bdist_msi
```

The MSI is written to `dist/`.

GitHub Actions also builds the MSI automatically on pushes, pull requests, manual runs, and version tags. Tag pushes like `v1.0.1` attach the generated MSI to the matching GitHub release.

## Quick Actions

- This PC
- File Explorer
- Open Desktop
- Open Downloads
- Open Documents
- Empty Recycle Bin
- Toggle Dark Mode
- Lock Screen
- Shutdown
- Restart
- Sign Out

## Settings

Settings are stored at:

```text
%APPDATA%\SpotlightLauncher\settings.json
```

Enable **Full user-folder scan** in Settings > Search if you want Utility Win to search beyond the common Desktop, Downloads, Documents, Pictures, Videos, and Music folders. It improves coverage while still skipping noisy folders such as AppData, caches, temp folders, `.git`, and `node_modules`.

## License

MIT
