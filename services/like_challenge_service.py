import threading
import time
# ÄNDERUNG: Importiere TikTokLive_API statt TikTokLiveClientWrapper
from external.TikTokLive_API import TikTokLive_API
from external.settings_manager import SettingsManager
from utils import server_log


class LikeChallengeService:
    def __init__(self):
        # Zeigt explizit auf die Like-Settings
        self.settings_manager = SettingsManager('like_overlay/settings.json')
        self.api_client = None
        self.is_running = False

    def start_tiktok_connection(self):
        """Startet die Verbindung basierend auf den gespeicherten Settings."""
        settings = self.settings_manager.load_settings()
        tiktok_id = settings.get("tiktok_unique_id", "")

        if tiktok_id:
            server_log.info(f"Starte TikTok-Verbindung zu @{tiktok_id}...")
            # ÄNDERUNG: Instanziierung der korrekten Klasse TikTokLive_API
            self.api_client = TikTokLive_API(tiktok_id)
            self.api_client.start()
            self.is_running = True
        else:
            server_log.warning("⚠️ Autostart: Kein TikTok-User in Settings gefunden (like_overlay/settings.json).")

    def update_and_restart(self, new_tiktok_id):
        """Wird von der GUI aufgerufen, um den Nutzer zu ändern."""
        if self.api_client:
            self.api_client.stop()
            time.sleep(1)

        # Speichern
        settings = self.settings_manager.load_settings()
        settings["tiktok_unique_id"] = new_tiktok_id
        self.settings_manager.save_settings(settings)

        # Neustart
        self.start_tiktok_connection()

    def get_challenge_status(self):
        """Liefert Daten für das Overlay."""
        current_likes = 0
        if self.api_client:
            current_likes = self.api_client.current_likes

        settings = self.settings_manager.load_settings()
        goal = int(settings.get("like_goal", 10000))

        return {
            "current_likes": current_likes,
            "goal": goal,
            "connected": self.api_client.is_connected if self.api_client else False,
            "tiktok_user": settings.get("tiktok_unique_id", "")
        }

    def add_test_likes(self, amount):
        if self.api_client:
            self.api_client.current_likes += amount