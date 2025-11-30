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

        # NEU: Test-Likes Speicher
        self.test_likes = 0

        self.previous_current_goal = None

    def add_test_likes(self, amount):
        """Fügt Test-Likes hinzu, um die Animationen zu testen."""
        self.test_likes += amount
        server_log.info(f"Test-Modus: {amount} Likes hinzugefügt. Total Test-Likes: {self.test_likes}")

    def evaluate_expression_safely(self, expression, x_value):
        """Wertet den mathematischen Ausdruck sicher aus."""
        allowed_names = {"x": x_value, "numpy": numpy, "np": numpy}
        allowed_builtins = {
            'abs': abs, 'int': int, 'float': float, 'round': round,
            'pow': pow, 'min': min, 'max': max, 'sum': sum
        }
        if "__" in expression:
            raise ValueError("Ungültiger Ausdruck in der Formel.")
        result = eval(expression, {"__builtins__": allowed_builtins}, allowed_names)
        return int(result)

    def _ensure_api_connection(self, tiktok_user):
        if not tiktok_user: return
        if self.api_client is None or self.current_monitored_user != tiktok_user:
            if self.api_client:
                try:
                    self.api_client.stop()
                except:
                    pass

            server_log.info(f"Initialisiere TikTok API für: {tiktok_user}")
            self.api_client = TikTokLive_API(tiktok_user)
            self.api_client.start()
            self.current_monitored_user = tiktok_user

    def start_tiktok_connection(self):
        """Lädt den Usernamen aus den Settings und startet die Verbindung sofort."""
        try:
            settings = self.settings_manager.load_settings()
            tiktok_user = settings.get("tiktok_unique_id", "")

            if tiktok_user:
                server_log.info(f"🔌 Autostart: Verbinde zu @{tiktok_user} ...")
                self._ensure_api_connection(tiktok_user)
            else:
                server_log.warning("⚠️ Autostart übersprungen: Kein TikTok-Username in den Einstellungen.")

        except Exception as e:
            server_log.error(f"❌ Fehler beim Autostart der TikTok-Verbindung: {e}")

    def force_start(self):
        """Alias für start_tiktok_connection (Kompatibilität)."""
        self.start_tiktok_connection()

    def get_challenge_status(self):
        """Berechnet den Status inkl. Test-Likes."""
        try:
            settings = self.settings_manager.load_settings()
        except FileNotFoundError:
            return {"error": "Settings fehlen"}

        tiktok_user = settings.get("tiktok_unique_id", "")
        display_format = settings.get("displayTextFormat", "{likes_needed} Likes bis zum nächsten Ziel")
        initial_goals = sorted(settings.get("initialGoals", []))
        recurring_expr = settings.get("recurringGoalExpression", "x + 33333")

        # Verbindung prüfen (falls noch nicht geschehen durch Autostart)
        if tiktok_user:
            self._ensure_api_connection(tiktok_user)

        # Echte Likes + Test Likes
        real_likes = 0
        if self.api_client:
            real_likes = self.api_client.get_current_likes()

        like_count = real_likes + self.test_likes

        # --- Geschäftslogik für Ziele ---
        current_goal = None
        last_checked_goal = 0

        for g in initial_goals:
            last_checked_goal = g
            if like_count < g:
                current_goal = g
                break

        if current_goal is None:
            if not initial_goals:
                last_checked_goal = 0
            else:
                last_checked_goal = initial_goals[-1]

            calculated_goal = self.evaluate_expression_safely(recurring_expr, last_checked_goal)
            loop_guard = 0
            while like_count >= calculated_goal and loop_guard < 1000:
                last_checked_goal = calculated_goal
                calculated_goal = self.evaluate_expression_safely(recurring_expr, last_checked_goal)
                if calculated_goal <= last_checked_goal:
                    calculated_goal = like_count + 1000
                    break
                loop_guard += 1
            current_goal = calculated_goal

        # --- Sound-Logik & HYPE EVENT (NEU) ---
        if self.previous_current_goal is None:
            self.previous_current_goal = current_goal

        # Wenn Ziel erreicht (Likes >= Ziel)
        if (self.previous_current_goal != current_goal) and (like_count >= self.previous_current_goal):
            from services.service_provider import audio_service_instance, subathon_service_instance

            server_log.info(f"Ziel {self.previous_current_goal} erreicht! (Likes: {like_count}) -> Sound & Hype Mode")

            # 1. Sound abspielen
            audio_service_instance.play_goal_sound()

            # 2. HYPE MODE Trigger (Event 5) - Startet für 5 Minuten (300s)
            # Das löst Event 5 aus: Doppelte Zeit für neue Zeit-Adds
            subathon_service_instance.trigger_hype_mode(300)

            self.previous_current_goal = current_goal

        if self.previous_current_goal != current_goal:
            self.previous_current_goal = current_goal

        likes_needed = max(0, int(current_goal - like_count))
        display_text = display_format.format(likes_needed=likes_needed)

        return {
            "like_count": int(like_count),
            "likes_needed": likes_needed,
            "current_goal": int(current_goal),
            "displayText": display_text
        }