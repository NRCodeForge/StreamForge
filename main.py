import sys
import os
import subprocess

# Importiere Datenbank-Setup und GUI
from database.db_setup import setup_database
from presentation.gui_app import StreamForgeGUI
from utils import server_log
from config import DATABASE_PATH

if __name__ == '__main__':
    # 1. Datenbank prüfen und initialisieren
    try:
        setup_database()
    except Exception as e:
        server_log.error(f"Fehler bei der Datenbankinitialisierung: {e}")
        sys.exit(1)

    # 2. GUI starten
    try:
        root = StreamForgeGUI()
        root.start()
    except Exception as e:
        server_log.error(f"Schwerwiegender Fehler in der GUI: {e}")
        sys.exit(1)