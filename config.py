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
API_ROOT = '/api'
WISHES_ENDPOINT = f'{API_ROOT}/wishes'
NEXT_WISH_ENDPOINT = f'{WISHES_ENDPOINT}/next'
RESET_WISHES_ENDPOINT = f'{WISHES_ENDPOINT}/reset'
LIKE_CHALLENGE_ENDPOINT = f'{API_ROOT}/like_challenge'

class Style:
    """Eine Klasse zur zentralen Verwaltung von UI-Stilkonstanten."""
    # Farbpalette
    BACKGROUND = "#2E2E2E"
    FOREGROUND = "#E0E0E0"
    BORDER = "#4A4A4A"
    SUCCESS = "#28A745"
    DANGER = "#DC3545"
    WARNING = "#FFC107"
    INFO = "#17A2B8"
    TEXT_MUTED = "#6C757D"
    PRIMARY = "#007BFF"

    # Schriftarten
    FONT_FAMILY = "Segoe UI"

# API-Endpunkte und Basiskonfiguration
BASE_HOST = "127.0.0.1"
BASE_PORT = 5000
BASE_URL = f"http://{BASE_HOST}:{BASE_PORT}"
RESET_WISHES_ENDPOINT = "/api/wishes/reset"
