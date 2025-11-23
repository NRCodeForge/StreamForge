"""
Startpunkt der Anwendung StreamForge.

- Fügt den Projekt-Root zum sys.path hinzu, damit absolute Importe zuverlässig funktionieren.
- Initialisiert die Datenbank (falls noch nicht vorhanden).
- Startet anschließend die Tkinter-GUI, die wiederum den Flask-Webserver im Hintergrund startet.

Dieses Skript enthält keine Geschäftslogik; es koordiniert lediglich den Anwendungsstart.
"""

import sys
import os


current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)
# ---------------------------------------------------------------

# Absolute Importe vom Projekt-Root
from database.db_setup import setup_database
from presentation.gui_app import StreamForgeGUI
from utils import server_log
from config import DATABASE_PATH

if __name__ == '__main__':
    # 1. Datenbank prüfen und initialisieren
    try:
        setup_database()
        server_log.info(f"Datenbankpfad: {DATABASE_PATH}")
    except Exception as e:
        server_log.error(f"Fehler bei der Datenbankinitialisierung: {e}")
        sys.exit(1)

    # 2. GUI starten
    try:
        app = StreamForgeGUI()
        app.start()
    except Exception as e:
        server_log.error(f"Schwerwiegender Fehler in der GUI: {e}")
        sys.exit(1)