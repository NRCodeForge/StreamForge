# StreamForge/services/like_challenge_service.py

import numpy as np
import json
import sys
from playwright.sync_api import sync_playwright

# KORREKTUR: Verwende absolute Imports
from external.settings_manager import SettingsManager
from external.tikfinity_client import TikfinityClient
from utils import server_log


class LikeChallengeService:
    """Verwaltet die Geschäftslogik für die Like Challenge."""

    def __init__(self):
        # SettingsManager wird mit dem relativen Pfad initialisiert, da get_path den Root des Projekts kennt
        self.settings_manager = SettingsManager('like_overlay/settings.json')
        self.tikfinity_client = TikfinityClient()

    def evaluate_expression_safely(self, expression, x_value):
        """Wertet den mathematischen Ausdruck sicher aus (aus app.py übernommen)."""
        allowed_names = {"x": x_value, "numpy": np, "np": np}
        if "__" in expression:
            raise ValueError("Ungültiger Ausdruck in der Formel.")

        # np/numpy muss im globalen Namensraum der eval-Funktion verfügbar sein.
        result = eval(expression, {"__builtins__": None}, allowed_names)
        return int(result)

    def get_challenge_status(self):
        """Berechnet den aktuellen Status der Like Challenge."""
        try:
            settings = self.settings_manager.load_settings()
        except FileNotFoundError:
            raise FileNotFoundError("Like Challenge settings.json fehlt.")

        widget_url = settings.get("widgetUrl")
        display_format = settings.get("displayTextFormat", "{likes_needed} Likes bis zum nächsten Ziel")
        initial_goals = settings.get("initialGoals", [])
        recurring_expr = settings.get("recurringGoalExpression", "x + 33333")

        if not widget_url:
            raise ValueError("widgetUrl fehlt in settings.json")

        # Rufe externe Daten über den Client ab
        like_count = self.tikfinity_client.fetch_like_count(widget_url)

        # --- Geschäftslogik zur Zielbestimmung ---
        current_goal = None
        for g in initial_goals:
            if like_count < g:
                current_goal = g
                break

        if current_goal is None and initial_goals:
            last_goal = initial_goals[-1]
            current_goal = self.evaluate_expression_safely(recurring_expr, last_goal)
        elif current_goal is None:
            # Fallback, falls keine initial goals definiert, aber eine Expression existiert
            current_goal = self.evaluate_expression_safely(recurring_expr, 0)

        likes_needed = int(current_goal - like_count)
        display_text = display_format.format(likes_needed=likes_needed)

        return {
            "like_count": int(like_count),
            "likes_needed": likes_needed,
            "current_goal": int(current_goal),
            "displayText": display_text
        }