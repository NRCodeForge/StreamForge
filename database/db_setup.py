import sqlite3  # <--- Dieser Import hat gefehlt!
from config import DATABASE_PATH
from utils import server_log

def setup_database():
    """Erstellt die notwendigen Tabellen für Wünsche und Währung."""
    conn = None
    try:
        # Verbindung herstellen
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()

        # 1. Tabelle: Killerwünsche (Existierende Tabelle)
        # Wir nutzen IF NOT EXISTS, damit bestehende Daten bleiben
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS killer_wuensche (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                wunsch TEXT NOT NULL,
                user_name TEXT NOT NULL,
                datum TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # 2. Tabelle: Currency (Neue Tabelle für Währung)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS currency (
                user_id TEXT PRIMARY KEY,
                user_name TEXT,
                amount INTEGER DEFAULT 0,
                last_seen DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        conn.commit()
        server_log.info("Datenbank und Tabellen (Wishes & Currency) erfolgreich geprüft.")

    except sqlite3.Error as e:
        server_log.error(f"Fehler bei der Datenbank-Initialisierung: {e}")
        # Wir raisen den Fehler, damit main.py das merkt und nicht weitermacht
        raise e
    finally:
        if conn:
            conn.close()