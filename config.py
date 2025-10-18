import os
import sys

# --- Pfad-Hilfsfunktion (aus app.py/new_gui.py) ---
def get_path(relative_path):
    """Gibt den korrekten absoluten Pfad für gebündelte Anwendungen (PyInstaller) zurück."""
    try:
        # Pfad im temporären PyInstaller-Verzeichnis
        base_path = sys._MEIPASS
    except Exception:
        # Normaler Ausführungspfad
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

# --- Globale Konstanten ---
DATABASE_NAME = 'killerwuensche.db'
DATABASE_PATH = get_path(DATABASE_NAME)

LOG_FILE_SERVER = get_path('server.log')
LOG_FILE_WISHES = get_path('wishes.log')

BASE_HOST = '127.0.0.1'
BASE_PORT = 5000
BASE_URL = f'http://{BASE_HOST}:{BASE_PORT}/'

# API Endpunkte
API_ROOT = '/api/v1' # Zentraler Präfix für alle APIs
WISHES_ENDPOINT = f'{API_ROOT}/wishes'
NEXT_WISH_ENDPOINT = f'{WISHES_ENDPOINT}/next'
RESET_WISHES_ENDPOINT = f'{WISHES_ENDPOINT}/reset'
LIKE_CHALLENGE_ENDPOINT = f'{API_ROOT}/like_challenge'

# UI Design (Aus new_gui.py kopiert)
class Style:
    BACKGROUND = "#1A1B26"
    WIDGET_BG = "#2A2C3A"
    FOREGROUND = "#E0E0E0"
    TEXT_MUTED = "#A6B0CF"
    ACCENT_BLUE = "#33B1FF"
    DANGER = "#FA4D56"
    FONT_FAMILY = "Roboto"