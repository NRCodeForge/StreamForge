import sqlite3
from ..config import DATABASE_PATH # relative import zum Hauptverzeichnis

def get_db_connection():
    """Stellt eine Verbindung zur Datenbank her und setzt row_factory auf sqlite3.Row."""
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    return conn