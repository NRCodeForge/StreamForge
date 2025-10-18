import sqlite3
import os
from .db_connector import get_db_connection

def setup_database():
    """Erstellt oder aktualisiert die Datenbanktabelle für die Killerwünsche."""
    try:
        conn = get_db_connection()
        c = conn.cursor()
        c.execute('''
            CREATE TABLE IF NOT EXISTS killer_wuensche (
                id INTEGER PRIMARY KEY,
                wunsch TEXT NOT NULL,
                user_name TEXT NOT NULL,
                datum TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        conn.commit()
        conn.close()
    except Exception as e:
        # Hier sollte besser ein dedizierter DB-Logger verwendet werden.
        print(f"Fehler beim Einrichten der Datenbank: {e}", file=sys.stderr)