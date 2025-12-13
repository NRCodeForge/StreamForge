"""
Startpunkt der Anwendung StreamForge.
"""
import sys
import os
import time

current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

from database.db_setup import setup_database
from presentation.gui_app import StreamForgeGUI
from utils import server_log
from config import DATABASE_PATH
from services.service_provider import like_service_instance, twitch_service_instance

if __name__ == '__main__':
    print("\n\n=== STREAMFORGE STARTUP ===")

    # 1. Datenbank
    try:
        setup_database()
        server_log.info(f"Datenbankpfad: {DATABASE_PATH}")
    except Exception as e:
        server_log.error(f"DB Fehler: {e}")
        sys.exit(1)

    # 2. TikTok Verbindung (Autostart)
    print(">>> Prüfe TikTok Verbindung...")
    try:
        like_service_instance.start_tiktok_connection()
    except Exception as e:
        server_log.error(f"FATAL: Konnte TikTok Service nicht starten: {e}")

    # 3. Twitch Verbindung (Autostart)
    print(">>> Prüfe Twitch Verbindung...")
    try:
        # Hier nutzen wir jetzt die neue Auto-Start Logik des Services
        twitch_service_instance.try_auto_start()
    except Exception as e:
        print(f"Twitch Autostart Fehler: {e}")

    # 4. GUI
    try:
        print(">>> Starte GUI...")
        app = StreamForgeGUI()
        app.start()
    except Exception as e:
        server_log.error(f"GUI Fehler: {e}")
        sys.exit(1)