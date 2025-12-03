import json
import numpy as numpy
import time

from external.settings_manager import SettingsManager
from utils import server_log
from external.TikTokLive_API import TikTokLive_API


class LikeChallengeService:
    def __init__(self):
        self.settings_manager = SettingsManager('like_overlay/settings.json')
        self.api_client = None
        self.current_monitored_user = None
        self.test_likes = 0
        self.previous_current_goal = None

    def add_test_likes(self, amount):
        self.test_likes += amount
        server_log.info(f"Test-Modus: {amount} Likes hinzugefügt. Total: {self.test_likes}")

    def evaluate_expression_safely(self, expression, x_value):
        allowed = {"x": x_value, "numpy": numpy, "np": numpy}
        if "__" in expression: raise ValueError("Ungültig")
        return int(eval(expression, {"__builtins__": {}}, allowed))

    def _ensure_api_connection(self, tiktok_user):
        if not tiktok_user: return
        # Nur neu verbinden, wenn User anders ist oder Client fehlt
        if self.api_client is None or self.current_monitored_user != tiktok_user:
            if self.api_client:
                try:
                    self.api_client.stop()
                except:
                    pass

            server_log.info(f"🚀 START: TikTok API Verbindung zu @{tiktok_user}")
            self.api_client = TikTokLive_API(tiktok_user)
            self.api_client.start()
            self.current_monitored_user = tiktok_user
        else:
            # Falls Client da ist aber nicht läuft -> Starten
            if not self.api_client.running:
                self.api_client.start()

    # --- WICHTIG: DIESE METHODE WIRD VOM HAUPTPROGRAMM GERUFEN ---
    def start_tiktok_connection(self):
        """Lädt Settings und startet Verbindung."""
        try:
            s = self.settings_manager.load_settings()
            user = s.get("tiktok_unique_id", "").strip()

            if user:
                server_log.info(f"⚙️ Autostart gefunden für: {user}")
                self._ensure_api_connection(user)
            else:
                server_log.warning(
                    "⚠️ KEIN TIKTOK USERNAME in den Einstellungen gefunden! Bitte im Dashboard eingeben.")
        except Exception as e:
            server_log.error(f"Fehler beim API Start: {e}")

    # --- NEU: Für die GUI zum Neustarten ---
    def update_and_restart(self, new_user):
        """Speichert neuen User und erzwingt Reconnect."""
        s = self.settings_manager.load_settings()
        s["tiktok_unique_id"] = new_user
        self.settings_manager.save_settings(s)

        server_log.info(f"🔄 Manueller Neustart für: {new_user}")
        # Erzwinge neue Verbindung
        self.current_monitored_user = None
        self._ensure_api_connection(new_user)

    def get_challenge_status(self):
        # (Hier dein bestehender Code für get_challenge_status - gekürzt für Übersicht)
        # Wichtig: Auch hier sicherstellen, dass Verbindung steht
        try:
            s = self.settings_manager.load_settings()
            user = s.get("tiktok_unique_id", "")
            if user: self._ensure_api_connection(user)

            real = self.api_client.get_current_likes() if self.api_client else 0
            total = real + self.test_likes

            # ... (Deine Logik für Goals) ...
            # Platzhalter Logik:
            needed = 1000 - (total % 1000)
            return {"like_count": total, "likes_needed": needed, "current_goal": total + needed,
                    "displayText": f"{needed} to go"}
        except:
            return {"error": "Init..."}