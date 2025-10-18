import json
import numpy as numpy
# Playwright wird hier nicht mehr direkt benötigt
# from playwright.sync_api import sync_playwright 

# Importiere Hilfsfunktionen aus anderen Schichten
from external.settings_manager import SettingsManager
from utils import server_log
from external.tikfinity_client import TikfinityClient  # <-- WICHTIG


class LikeChallengeService:
    def __init__(self):
        self.settings_manager = SettingsManager('like_overlay/settings.json')
        # Der Client wird "Lazy" initialisiert, da wir die URL erst später bekommen
        self.client = None

        # ... (deine evaluate_expression_safely Methode bleibt unverändert) ...

    def evaluate_expression_safely(self, expression, x_value):
        """Wertet den mathematischen Ausdruck sicher aus (aus app.py übernommen)."""
        allowed_names = {"x": x_value, "numpy": numpy, "np": numpy}
        if "__" in expression:
            raise ValueError("Ungültiger Ausdruck in der Formel.")
        result = eval(expression, {"__builtins__": {}}, allowed_names)
        return int(result)

    def get_challenge_status(self):
        """Berechnet den aktuellen Status der Like Challenge."""
        try:
            settings = self.settings_manager.load_settings()
        except FileNotFoundError:
            server_log.error("settings.json für Like Challenge nicht gefunden.")
            raise FileNotFoundError("Like Challenge settings.json fehlt.")

        widget_url = settings.get("widgetUrl")
        display_format = settings.get("displayTextFormat", "{likes_needed} Likes bis zum nächsten Ziel")
        initial_goals = settings.get("initialGoals", [])
        recurring_expr = settings.get("recurringGoalExpression", "x + 33333")

        if not widget_url:
            raise ValueError("widgetUrl fehlt in settings.json")

        # --- Externe Integration (Monitoring-Thread) ---

        # Initialisiere den Client und starte den Monitor-Thread (nur beim ersten Mal)
        if self.client is None:
            server_log.info("Initialisiere Tikfinity-Monitor-Service...")
            self.client = TikfinityClient(widget_url)
            self.client.start_monitoring()


            # Ruft den zwischengespeicherten Wert schnell ab
        like_count = self.client.get_current_like_count()

        # --- Geschäftslogik zur Zielbestimmung ---
        current_goal = None
        for g in initial_goals:
            if like_count < g:
                current_goal = g
                break

        # ... (Rest der Methode bleibt gleich) ...
        if current_goal is None and initial_goals:
            last_goal = initial_goals[-1]
            current_goal = self.evaluate_expression_safely(recurring_expr, last_goal)
        elif current_goal is None:
            current_goal = self.evaluate_expression_safely(recurring_expr, 0)

        likes_needed = int(current_goal - like_count)
        display_text = display_format.format(likes_needed=likes_needed)

        return {
            "like_count": int(like_count),
            "likes_needed": likes_needed,
            "current_goal": int(current_goal),
            "displayText": display_text
        }

