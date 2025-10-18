import sys
from .db_connector import get_db_connection
from utils import server_log

def setup_database():
    """Erstellt oder aktualisiert die Datenbanktabelle für die Killerwünsche."""
    try:
        conn = get_db_connection() # <-- MÖGLICHER FEHLER HIER
        conn.execute('''
                  CREATE TABLE IF NOT EXISTS killer_wuensche
                  (
                      id
                      INTEGER
                      PRIMARY
                      KEY,
                      wunsch
                      TEXT
                      NOT
                      NULL,
                      user_name
                      TEXT
                      NOT
                      NULL,
                      datum
                      TIMESTAMP
                      DEFAULT
                      CURRENT_TIMESTAMP
                  )
                  ''')
        conn.close()
        server_log.info("Datenbank und Tabelle erfolgreich erstellt oder aktualisiert.")
    except Exception as e:
        server_log.error(f"Fehler beim Einrichten der Datenbank: {e}")
        raise

