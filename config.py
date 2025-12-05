import os
import sys


# --- Pfad-Hilfsfunktion für mitgelieferte Dateien (Lesen) ---
def get_path(relative_path):
    """
    Gibt den korrekten absoluten Pfad für gebündelte Dateien (Assets, Overlays etc.) zurück,
    egal ob als --onefile oder Verzeichnis gebündelt.
    """
    if getattr(sys, 'frozen', False):
        # Wir sind in einer gebündelten Anwendung
        if hasattr(sys, '_MEIPASS'):
            # --onefile Modus: Dateien sind im temporären _MEIPASS Ordner
            base_path = sys._MEIPASS
        else:
            # Verzeichnis (onedir) Modus: Dateien sind relativ zur EXE
            base_path = os.path.dirname(sys.executable)
    else:
        # Normale Ausführung als Skript
        base_path = os.path.abspath(os.path.dirname(os.path.abspath(__file__)))

    # Manchmal gibt PyInstaller Pfade mit falschen Slashes zurück, normalisieren wir sie
    normalized_path = os.path.normpath(os.path.join(base_path, relative_path))
    return normalized_path


# --- Funktion für schreibbare, persistente Dateien (Logs, geänderte Settings) ---
def get_persistent_path(relative_path):
    """
    Gibt den korrekten, *schreibbaren* Pfad für persistente Dateien zurück.
    Diese werden neben der EXE-Datei oder dem Skript gespeichert.
    """
    if getattr(sys, 'frozen', False):
        # Gebündelte Anwendung (EXE)
        base_path = os.path.dirname(sys.executable)
    else:
        # Normales Python-Skript
        base_path = os.path.abspath(os.path.dirname(os.path.abspath(__file__)))

    # Stelle sicher, dass das Verzeichnis existiert
    target_dir = os.path.dirname(os.path.join(base_path, relative_path))
    if target_dir:  # Nur erstellen, wenn es nicht das Hauptverzeichnis ist
        os.makedirs(target_dir, exist_ok=True)

    normalized_path = os.path.normpath(os.path.join(base_path, relative_path))
    return normalized_path


# --- Globale Konstanten ---
DATABASE_NAME = 'database.db'

# --- LOGIK-ÄNDERUNG: DATENBANK IM ELTERNVERZEICHNIS ---
# 1. Bestimme das aktuelle Verzeichnis der Anwendung (wo die EXE/das Skript liegt)
if getattr(sys, 'frozen', False):
    _app_dir = os.path.dirname(sys.executable)
else:
    _app_dir = os.path.abspath(os.path.dirname(os.path.abspath(__file__)))

# 2. Gehe einen Ordner nach oben (Parent Directory)
_parent_dir = os.path.dirname(_app_dir)

# 3. Setze den Datenbankpfad auf ../killerwuensche.db
DATABASE_PATH = os.path.join(_parent_dir, DATABASE_NAME)


# Logs bleiben im Anwendungs-Ordner (optional änderbar, falls gewünscht)
LOG_FILE_SERVER = get_persistent_path('server.log')
LOG_FILE_WISHES = get_persistent_path('wishes.log')

BASE_HOST = '127.0.0.1'
BASE_PORT = 5000
BASE_URL = f'http://{BASE_HOST}:{BASE_PORT}'

# API Endpunkte
API_ROOT = '/api/v1/'
WISHES_ENDPOINT = f'{API_ROOT}/wishes'
NEXT_WISH_ENDPOINT = f'{WISHES_ENDPOINT}/next'
RESET_WISHES_ENDPOINT = f'{WISHES_ENDPOINT}/reset'
LIKE_CHALLENGE_ENDPOINT = f'{API_ROOT}/like_challenge'
COMMANDS_ENDPOINT = f'{API_ROOT}/commands'
COMMANDS_TRIGGER_ENDPOINT = f'{COMMANDS_ENDPOINT}/trigger'

# UI Design
class Style:
    BACKGROUND = "#1A1B26"
    WIDGET_BG = "#2A2C3A"
    FOREGROUND = "#E0E0E0"
    TEXT_MUTED = "#A6B0CF"
    ACCENT_BLUE = "#33B1FF"
    DANGER = "#FA4D56"
    FONT_FAMILY = "Roboto"
    BORDER = "#3A3C4A"
    WIDGET_HOVER = "#3A3C4A"
    ACCENT_PURPLE = "#7E57C2"
    SUCCESS = "#4CAF50"