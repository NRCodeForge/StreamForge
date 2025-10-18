import json
import numpy as numpy  # numpy muss hier importiert und bereitgestellt werden
from playwright.sync_api import sync_playwright

# Importiere Hilfsfunktionen aus anderen Schichten
from external.settings_manager import SettingsManager
from utils import server_log


class LikeChallengeService:
    def __init__(self):
        # SettingsManager würde für settings.json zuständig sein
        self.settings_manager = SettingsManager('like_overlay/settings.json')

        # Eval ist riskant, aber aus dem Originalcode übernommen;

    # es wird hier im Service Layer isoliert und mit Allowed Names abgesichert.
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

        # --- Externe Integration (Web Scraping) ---
        # Dies wird idealerweise in einer eigenen Klasse (external/tikfinity_client.py) gekapselt.
        # Hier wird der Einfachheit halber der Originalcode aus app.py verwendet.
        like_count = self._fetch_like_count(widget_url)

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

    def _fetch_like_count(self, widget_url):
        # **WARNUNG:** Playwright ist hier synchron und blockiert.
        # In einer sauberen Architektur sollte dies ausgelagert oder asynchron gemacht werden.
        # Aber für die Refaktorierung des Originalcodes:
        with sync_playwright() as p:
            browser = p.firefox.launch(headless=True)
            page = browser.new_page()
            page.goto(widget_url, wait_until="load")
            page.wait_for_function("window.lastPercentValue !== undefined")
            value = page.evaluate("window.lastPercentValue")
            browser.close()

        if value is None:
            raise ValueError("lastPercentValue nicht gefunden")

        return value / 10