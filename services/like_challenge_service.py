import threading
import time
# Wir brauchen LikeEvent, um live zu reagieren
from TikTokLive.events import LikeEvent
from external.TikTokLive_API import TikTokLive_API
from external.settings_manager import SettingsManager
from utils import server_log


class LikeChallengeService:
    def __init__(self):
        # Pfad zur JSON-Datei. SettingsManager kümmert sich um das Laden/Speichern.
        self.settings_file = 'like_overlay/settings.json'
        self.settings_manager = SettingsManager(self.settings_file)
        self.api_client = None
        self.is_running = False

    def start_tiktok_connection(self):
        settings = self.settings_manager.load_settings()
        tiktok_id = settings.get("tiktok_unique_id", "")

        if tiktok_id:
            server_log.info(f"Starte TikTok-Verbindung zu @{tiktok_id}...")
            self.api_client = TikTokLive_API(tiktok_id)

            # WICHTIG: Listener registrieren, damit wir Likes mitbekommen!
            self.api_client.add_listener(self._on_tiktok_event)

            self.api_client.start()
            self.is_running = True
        else:
            server_log.warning("⚠️ Kein TikTok-User in Settings (like_overlay/settings.json).")

    def update_and_restart(self, new_tiktok_id):
        if self.api_client:
            self.api_client.stop()
            time.sleep(1)

        s = self.settings_manager.load_settings()
        s["tiktok_unique_id"] = new_tiktok_id
        self.settings_manager.save_settings(s)
        self.start_tiktok_connection()

    def get_challenge_status(self):
        current_likes = 0
        if self.api_client:
            current_likes = self.api_client.current_likes

        settings = self.settings_manager.load_settings()

        # NEU: Das passende Ziel basierend auf den Likes ermitteln
        goal = self._get_appropriate_goal(current_likes, settings)

        # Optional: Das Ziel in der settings.json synchronisieren,
        # damit es auch in der Datei aktuell bleibt
        if settings.get("like_goal") != goal:
            self._save_new_goal(goal)

        fmt = settings.get("displayTextFormat", "{current} / {goal}")
        likes_needed = max(0, goal - current_likes)

        try:
            display_text = fmt.format(
                likes_needed=likes_needed,
                current=current_likes,
                goal=goal
            )
        except Exception:
            display_text = f"{current_likes} / {goal}"

        return {
            "current_likes": current_likes,
            "goal": goal,
            "display_text": display_text,
            "tiktok_user": settings.get("tiktok_unique_id", "")
        }

    def add_test_likes(self, amount):
        if self.api_client:
            self.api_client.current_likes += amount
            # Auch bei Test-Likes prüfen wir das Ziel!
            self._check_goal_progression(self.api_client.current_likes)

    # --- INTERNE LOGIK ---

    def _on_tiktok_event(self, event):
        """Wird bei JEDEM TikTok Event aufgerufen."""
        if isinstance(event, LikeEvent):
            # Prüfen, ob Ziel erreicht wurde
            self._check_goal_progression(self.api_client.current_likes)

    def _check_goal_progression(self, current_likes):
        settings = self.settings_manager.load_settings()
        current_goal = int(settings.get("like_goal", 10000))

        # Wenn Ziel erreicht ist...
        if current_likes >= current_goal:
            server_log.info(f"🎉 ZIEL ERREICHT: {current_likes} >= {current_goal}")

            # 1. Sound abspielen
            try:
                # Import innerhalb der Funktion, um Zirkelbezüge zu vermeiden
                from services.service_provider import audio_service_instance
                audio_service_instance.play_goal_sound()
            except Exception as e:
                server_log.error(f"Sound Fehler: {e}")

            # 2. Neues Ziel berechnen
            next_goal = self._calculate_next_goal(current_goal, settings)
            server_log.info(f"➡ Neues Ziel: {next_goal}")

            # 3. Neues Ziel speichern
            self._save_new_goal(next_goal)

    def _calculate_next_goal(self, current_goal, settings):
        initial_goals = settings.get("initialGoals", [])

        # Wenn wir noch in der Start-Liste sind, nimm das nächste
        if current_goal in initial_goals:
            idx = initial_goals.index(current_goal)
            if idx + 1 < len(initial_goals):
                return initial_goals[idx + 1]

        # Sonst Formel anwenden (z.B. x + 10000)
        expression = settings.get("recurringGoalExpression", "x + 10000")
        try:
            return int(eval(str(expression), {"x": current_goal}))
        except:
            return current_goal + 10000

    def _save_new_goal(self, new_goal):
        s = self.settings_manager.load_settings()
        s["like_goal"] = new_goal
        self.settings_manager.save_settings(s)

    def _get_appropriate_goal(self, current_likes, settings):
        """Findet das kleinste Ziel, das über den aktuellen Likes liegt."""
        initial_goals = settings.get("initialGoals", [])

        # 1. Sortierte Liste der initialen Ziele prüfen
        sorted_goals = sorted([int(g) for g in initial_goals])
        for goal in sorted_goals:
            if goal > current_likes:
                return goal

        # 2. Falls wir über allen initialen Zielen liegen, Formel anwenden
        current_g = sorted_goals[-1] if sorted_goals else 0
        expression = settings.get("recurringGoalExpression", "x + 10000")

        # Wir wenden die Formel an, bis wir ein Ziel finden, das > current_likes ist
        # (Sicherheitshalber auf 100 Iterationen begrenzt)
        for _ in range(100):
            try:
                next_g = int(eval(str(expression), {"x": current_g}))
                if next_g <= current_g:  # Verhindert Endlosschleife
                    next_g = current_g + 10000
                current_g = next_g
            except:
                current_g += 10000

            if current_g > current_likes:
                return current_g

        return current_g