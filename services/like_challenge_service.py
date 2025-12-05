import json
import numpy as numpy
import time
import threading

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
        self.connect_lock = threading.Lock()

    def add_test_likes(self, amount):
        self.test_likes += amount
        server_log.info(f"TEST: {amount} Likes hinzugefügt. Total: {self.test_likes}")

    def evaluate_expression_safely(self, expression, x_value):
        """
        Wertet die Formel aus. Akzeptiert jetzt 'x' UND 'X'.
        Loggt Fehler, statt sie zu verschlucken.
        """
        allowed_names = {"x": x_value, "X": x_value, "numpy": numpy, "np": numpy}

        if "__" in expression:
            server_log.warning(f"Sicherheitswarnung: Ungültige Formel '{expression}'")
            return x_value + 1000

        try:
            result = eval(expression, {"__builtins__": {}}, allowed_names)
            return int(result)
        except Exception as e:
            server_log.error(f"❌ FORMEL-FEHLER bei '{expression}': {e}. Nutze Fallback (+1000).")
            return x_value + 1000

    def _ensure_api_connection(self, tiktok_user):
        if not tiktok_user: return
        with self.connect_lock:
            if self.api_client is None or self.current_monitored_user != tiktok_user:
                self._restart_client(tiktok_user)
            elif not self.api_client.running:
                server_log.warning(f"⚠️ TikTok-Client für {tiktok_user} war gestoppt. Starte neu...")
                self.api_client.start()

    def _restart_client(self, tiktok_user):
        if self.api_client:
            try:
                self.api_client.stop()
            except:
                pass

        # --- UPDATE START ---
        # Lade den Euler-Key aus den Settings
        try:
            s = self.settings_manager.load_settings()
            custom_key = s.get("euler_key", None)
        except:
            custom_key = None

        server_log.info(f"🚀 START: TikTok API Verbindung zu @{tiktok_user}")

        # Key an die API übergeben
        self.api_client = TikTokLive_API(tiktok_user, euler_key=custom_key)
        # --- UPDATE END ---

        self.api_client.start()
        self.current_monitored_user = tiktok_user

    def start_tiktok_connection(self):
        try:
            s = self.settings_manager.load_settings()
            user = s.get("tiktok_unique_id", "").strip()
            if user:
                server_log.info(f"⚙️ Autostart gefunden für: {user}")
                self._ensure_api_connection(user)
            else:
                server_log.warning("⚠️ Autostart: Kein TikTok-User in Settings gefunden.")
        except Exception as e:
            server_log.error(f"Fehler beim API Start: {e}")

    def update_and_restart(self, new_user):
        s = self.settings_manager.load_settings()
        s["tiktok_unique_id"] = new_user
        # Anmerkung: Der Key wird bereits in der GUI gespeichert,
        # hier speichern wir nur sicherheitshalber nochmal den User.
        self.settings_manager.save_settings(s)

        server_log.info(f"🔄 Manueller Neustart via GUI für: {new_user}")
        with self.connect_lock:
            self.current_monitored_user = None
            self._ensure_api_connection(new_user)

    def get_challenge_status(self):
        try:
            settings = self.settings_manager.load_settings()
            tiktok_user = settings.get("tiktok_unique_id", "").strip()
            if tiktok_user:
                self._ensure_api_connection(tiktok_user)
            else:
                return {"error": "Kein TikTok-Name", "displayText": "Setup in Dashboard"}

            real_likes = self.api_client.get_current_likes() if self.api_client else 0
            total_likes = real_likes + self.test_likes

            display_format = settings.get("displayTextFormat", "{likes_needed} to go")
            initial_goals = sorted(settings.get("initialGoals", []))

            recurring_expr = settings.get("recurringGoalExpression", "")
            if not recurring_expr or not recurring_expr.strip():
                recurring_expr = "x + 1000"

            current_goal = None

            for g in initial_goals:
                if total_likes < g:
                    current_goal = g
                    break

            if current_goal is None:
                calc = initial_goals[-1] if initial_goals else 0
                limit = 2000000
                found = False

                for _ in range(limit):
                    new_calc = self.evaluate_expression_safely(recurring_expr, calc)
                    if new_calc <= calc:
                        server_log.error(
                            f"❌ KRITISCH: Formel '{recurring_expr}' erhöht den Wert nicht! (Von {calc} auf {new_calc})")
                        calc = total_likes + 33333
                        found = True
                        break

                    calc = new_calc

                    if calc > total_likes:
                        found = True
                        break

                current_goal = calc

                if not found:
                    server_log.warning("⚠️ Loop-Limit bei Zielberechnung erreicht. Nutze Fallback auf aktuelle Likes.")
                    current_goal = self.evaluate_expression_safely(recurring_expr, total_likes)

            if self.previous_current_goal is None:
                self.previous_current_goal = current_goal

            if (self.previous_current_goal != current_goal) and (total_likes >= self.previous_current_goal):
                from services.service_provider import audio_service_instance, subathon_service_instance
                server_log.info(f"🎉 ZIEL ERREICHT: {self.previous_current_goal} (Likes: {total_likes})")
                audio_service_instance.play_goal_sound()
                subathon_service_instance.trigger_hype_mode(300)
                self.previous_current_goal = current_goal

            if self.previous_current_goal != current_goal:
                self.previous_current_goal = current_goal

            likes_needed = max(0, int(current_goal - total_likes))
            display_text = display_format.format(likes_needed=likes_needed)

            return {
                "like_count": int(total_likes),
                "likes_needed": likes_needed,
                "current_goal": int(current_goal),
                "displayText": display_text
            }

        except Exception as e:
            server_log.error(f"Fehler im Like-Service: {e}")
            return {"error": "Interner Fehler", "displayText": "Server Error"}