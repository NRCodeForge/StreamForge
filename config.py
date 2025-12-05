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


# --- Funktion für schreibbare, persistente Dateien (Logs, DB, geänderte Settings) ---
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
DATABASE_NAME = 'killerwuensche.db'
DATABASE_PATH = get_persistent_path(DATABASE_NAME)  # Bleibt persistent

LOG_FILE_SERVER = get_persistent_path('server.log')  # Bleibt persistent
LOG_FILE_WISHES = get_persistent_path('wishes.log')  # Bleibt persistent

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


# --- DBD THEME STYLE DEFINITION ---
class Style:
    # --- Palette: Dead by Daylight Inspired ---
    BG_MAIN = "#0f0f13"  # Sehr dunkles, fast schwarzes Grau (Hintergrund)
    BG_CARD = "#1c1c24"  # UI Elemente Hintergrund (Karten)
    BG_INPUT = "#2b2b30"  # Eingabefelder

    # --- Accents ---
    ACCENT_RED = "#c0392b"  # DBD Blutrot (Primary Action)
    ACCENT_RED_HOVER = "#e74c3c"

    ACCENT_PURPLE = "#8e44ad"  # Twitch / Ultra Rare PerkVibe
    ACCENT_BLUE = "#2980b9"  # TikTok / Rare Perk Vibe

    BORDER = "#3f3f46"  # Subtile Ränder

    # --- Status Colors ---
    SUCCESS = "#27ae60"  # Grün
    WARNING = "#f39c12"  # Orange
    DANGER = "#c0392b"  # Rot

    # --- Typography ---
    TEXT_MAIN = "#ecf0f1"  # Helles Grau/Weiß
    TEXT_DIM = "#95a5a6"  # Gedimmter Text (Beschreibungen)

    FONT_HEADER = ("Segoe UI", 14, "bold")
    FONT_TITLE = ("Segoe UI", 20, "bold")
    FONT_BODY = ("Segoe UI", 10)
    FONT_MONO = ("Consolas", 9)

    # --- Legacy Fallback (Verhindert Crashs bei altem Code) ---
    FOREGROUND = TEXT_MAIN
    BACKGROUND = BG_MAIN
    CARD_BG = BG_CARD
    ACCENT_TWITCH = ACCENT_PURPLE