import os
import sys

# --- Pfad-Hilfsfunktion (aus app.py/new_gui.py) ---
def get_path(relative_path):
    """Gibt den korrekten absoluten Pfad für gebündelte Anwendungen (PyInstaller) zurück."""
    try:
        # Pfad im temporären PyInstaller-Verzeichnis
        base_path = sys._MEIPASS
    except Exception:
        # Normaler Ausführungspfad, ausgehend vom Verzeichnis der config.py
        base_path = os.path.abspath(os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base_path, relative_path)

# --- Globale Konstanten ---
DATABASE_NAME = 'killerwuensche.db'
DATABASE_PATH = get_path(DATABASE_NAME)

LOG_FILE_SERVER = get_path('server.log')
LOG_FILE_WISHES = get_path('wishes.log')

BASE_HOST = '127.0.0.1'
BASE_PORT = 5000
BASE_URL = f'http://{BASE_HOST}:{BASE_PORT}'

# API Endpunkte (Wird in web_api.py verwendet)
API_ROOT = '/api/v1/'
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
    BORDER = "#3A3C4A"
    WIDGET_HOVER = "#3A3C4A"
    ACCENT_PURPLE = "#7E57C2"
    SUCCESS = "#4CAF50"
