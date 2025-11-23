# StreamForge

StreamForge is a desktop manager for stream overlays with a built‑in local web API. It provides a Tkinter GUI to start a Flask server that serves multiple overlay UIs (Wishlist, Subathon, Timer, Like Challenge). It also integrates with an external Tikfinity widget via Playwright to track live like counts and can play sounds when goals are reached.

The application can be run from source (Python) or packaged as a Windows executable using PyInstaller (spec file included).

Spec run task: pyinstaller StreamForge.spec --clean --noconfirm

---
# Todo´s

QOL - PoP OUT für die Letzten 10 Killer

- !command einbindung "Twitch"
- Like Balken
- Killer Wunsch Platz per Befehl !place zb?
- UI Elements neues design?

 ...




---

## Stack and Project Details
- Language: Python
- Frameworks/Libraries:
  - GUI: Tkinter, Pillow (PIL)
  - Web API: Flask
  - Input/Hotkeys: pynput
  - Browser automation: Playwright (Firefox)
  - Audio: pygame
  - HTTP: requests
  - Data/Math: sqlite3 (standard library), numpy
- Packaging: PyInstaller (StreamForge.spec)
- OS target: Windows (paths and packaging are Windows‑oriented)

Entry points:
- Development: python main.py
- Packaged app: built .exe via PyInstaller spec (see Build section)

Main processes/threads:
- Tkinter GUI (main thread)
- Flask web server (background thread started by GUI)
- Playwright Firefox monitor thread for Tikfinity like count (background)
- Optional audio playback thread (pygame)


## Overview of Features
- Start/stop a local Flask server from a GUI
- Serve the following overlays as static web content:
  - /killer_wishes/… (Wishlist)
  - /subathon_overlay/…
  - /timer_overlay/…
  - /like_overlay/…
- API endpoints for managing a wishlist database and like challenge data
- Global hotkey: Page Down triggers “next wish”
- Copy overlay URLs directly from the GUI
- Persisted sqlite database file and UTF‑8 logs located next to the executable or script


## Requirements
- Windows 10/11
- Python 3.10+ (Tkinter included with most Python Windows installers)
- System dependencies:
  - Playwright browsers (Firefox) must be installed at development time
- Python packages (see Install section): flask, requests, pillow, pygame, numpy, pynput, playwright

Note: No requirements.txt/pyproject.toml was found in the repository. The list above is derived from imports in the code.


## Install (from source)
Using PowerShell on Windows:

1) Create and activate a virtual environment
- py -3 -m venv .venv
- .\.venv\Scripts\Activate.ps1

2) Install Python dependencies
- pip install flask requests pillow pygame numpy pynput playwright

3) Install Playwright browsers (Firefox)
- python -m playwright install firefox

If Playwright CLI is not on PATH, call it via module as shown above.


## Run (development)
- Ensure the virtual environment is active (.\.venv\Scripts\Activate.ps1)
- Start the GUI (which also starts the web server):
  - python main.py

Once running, the GUI will automatically start the Flask server on 127.0.0.1:5000. The cards in the GUI show overlay names and allow copying their URLs. The Page Down key will advance to the next wish when the server is online.


## Build (Windows, PyInstaller)
A PyInstaller spec file is provided.

- pip install pyinstaller
- pyinstaller -y StreamForge.spec

Artifacts are placed under dist/. The application bundles assets and can optionally include Playwright files. If using the Like Challenge with Playwright in the packaged app, ensure the ms-playwright firefox artifacts are available alongside the executable. See timer_overlay/test.py for a helper script that prints the likely ms-playwright path on your machine.


## Configuration and Environment
Most configuration is embedded as constants in config.py:
- BASE_HOST = 127.0.0.1
- BASE_PORT = 5000
- DATABASE_NAME = killerwuensche.db
- Persistent paths and log files are resolved via get_persistent_path in config.py.

Overlay settings are stored as JSON files and managed by external/SettingsManager:
- like_overlay/settings.json
  - keys used: widgetUrl, displayTextFormat, initialGoals[], recurringGoalExpression
- subathon_overlay/settings.json

Tikfinity widget integration:
- external/tikfinity_client.py uses Playwright Firefox. When packaged, it attempts to use a bundled ms-playwright/firefox-*/firefox/firefox.exe under the app directory; otherwise it falls back to a system Playwright installation.

Environment variables:
- None are required by default.
- TODO: Consider allowing BASE_HOST/BASE_PORT and database path to be overridden via environment variables for advanced setups.


## API Endpoints (served by Flask)
Base URL: http://127.0.0.1:5000

Wishlist
- GET /api/v1//wishes → returns the current two wishes at the current offset
- POST /api/v1//wishes {"wunsch": string, "user_name": string} → add a wish
- POST /api/v1//wishes/next → advance offset (used by Page Down hotkey)
- POST /api/v1//wishes/reset → delete all wishes

Like Challenge
- GET /api/v1//like_challenge → returns { like_count, likes_needed, current_goal, displayText }

Static overlays
- /killer_wishes/<path>
- /timer_overlay/<path>
- /subathon_overlay/<path>
- /like_overlay/<path>

Note: The double slash in the path above reflects how constants are concatenated in code; the Flask router handles these correctly when invoked via the GUI‑constructed URLs.


## Scripts and Utilities
- main.py — entry point; initializes database and launches GUI + server
- presentation/web_api.py — Flask app and routes
- presentation/gui_app.py — Tkinter GUI, starts Flask in a thread
- presentation/ui_elements.py — widgets, copy URL, hotkey listener (Page Down)
- services/* — business logic layers (wishlist, like challenge, subathon, audio)
- external/tikfinity_client.py — Playwright Firefox monitor reading window.lastPercentValue from Tikfinity widget
- external/settings_manager.py — JSON settings loader/saver
- database/* — sqlite connector, initialization, and repository
- timer_overlay/test.py — helper for locating Playwright browser install path


## Project Structure (key parts)
- assets/ — icons and audio (e.g., icon.ico, sound.mp3)
- database/
  - db_connector.py, db_setup.py, wish_repository.py
- external/
  - settings_manager.py, tikfinity_client.py
- like_overlay/ — static files and settings.json for Like Challenge overlay
- subathon_overlay/ — static files and settings.json for Subathon overlay
- timer_overlay/ — static files; includes test.py helper
- killer_wishes/ — static files for Wishlist overlay
- presentation/
  - gui_app.py, web_api.py, ui_elements.py, settings_windows.py
- services/
  - like_challenge_service.py, subathon_service.py, wish_service.py, audio_service.py
- main.py — app launcher
- config.py — paths, constants, styles
- utils.py — logging setup (server.log, wishes.log)
- StreamForge.spec — PyInstaller spec


## Testing
- No automated unit tests were found.
- A helper script exists at timer_overlay/test.py to assist with Playwright browser path detection.
- TODO: Add unit tests for services and API routes (e.g., using pytest + Flask test client), and integration tests for Playwright‑dependent logic guarded by feature flags.


## Known Caveats
- Playwright Firefox must be installed for the Like Challenge integration to work when running from source. For packaged builds, ensure the appropriate ms-playwright assets are distributed with the executable.
- Pygame mixer initialization requires an audio device; on headless systems it may fail gracefully per logs.


## License
- No explicit license file was found in this repository.
- TODO: Add a LICENSE file (e.g., MIT) and update this section accordingly.