import json
import numpy as numpy
import time # Hinzugefügt für time.sleep, falls benötigt (obwohl es im Client verwendet wird)

# Importiere Hilfsfunktionen aus anderen Schichten
from external.settings_manager import SettingsManager
from utils import server_log
from external.tikfinity_client import TikfinityClient


# KORREKTUR: Der Import von 'audio_service_instance' wird von hier entfernt,
# um den Zirkelbezug zu durchbrechen.


class LikeChallengeService:
    def __init__(self):
        self.settings_manager = SettingsManager('like_overlay/settings.json')
        self.client = None
        # Speichert das Ziel vom letzten Aufruf, um Änderungen zu erkennen
        self.previous_current_goal = None

    def evaluate_expression_safely(self, expression, x_value):
        """Wertet den mathematischen Ausdruck sicher aus (aus app.py übernommen)."""
        allowed_names = {"x": x_value, "numpy": numpy, "np": numpy}
        # Erlaube grundlegende mathematische Operationen sicher
        allowed_builtins = {
            'abs': abs, 'int': int, 'float': float, 'round': round,
            'pow': pow, 'min': min, 'max': max, 'sum': sum
        }
        if "__" in expression:
            raise ValueError("Ungültiger Ausdruck in der Formel.")
        # Verwende eine eingeschränkte Umgebung für eval
        result = eval(expression, {"__builtins__": allowed_builtins}, allowed_names)
        return int(result) # Stelle sicher, dass das Ergebnis ein Integer ist

    def get_challenge_status(self):
        """Berechnet den aktuellen Status der Like Challenge."""
        try:
            settings = self.settings_manager.load_settings()
        except FileNotFoundError:
            server_log.error("settings.json für Like Challenge nicht gefunden.")
            raise FileNotFoundError("Like Challenge settings.json fehlt.")

        widget_url = settings.get("widgetUrl")
        display_format = settings.get("displayTextFormat", "{likes_needed} Likes bis zum nächsten Ziel")
        initial_goals = sorted(settings.get("initialGoals", [])) # Stelle sicher, dass sie sortiert sind
        recurring_expr = settings.get("recurringGoalExpression", "x + 33333")

        if not widget_url:
            raise ValueError("widgetUrl fehlt in settings.json")

        # --- Externe Integration (Monitoring-Thread) ---

        if self.client is None:
            server_log.info("Initialisiere Tikfinity-Monitor-Service...")
            self.client = TikfinityClient(widget_url)
            self.client.start_monitoring()

        like_count = self.client.get_current_like_count()

        # --- Geschäftslogik zur Zielbestimmung (KORRIGIERT) ---
        current_goal = None
        last_checked_goal = 0 # Startwert für die rekursive Berechnung

        # 1. Prüfe die initialen Ziele (die jetzt sortiert sind)
        for g in initial_goals:
            last_checked_goal = g # Merke dir das letzte geprüfte initiale Ziel
            if like_count < g:
                current_goal = g
                break # Erstes passendes initiales Ziel gefunden

        # 2. Wenn kein initiales Ziel gepasst hat (oder die Liste leer war)
        if current_goal is None:
            # Beginne die rekursive Berechnung entweder bei 0 (wenn initialGoals leer war)
            # oder beim letzten (höchsten) initialen Ziel.
            if not initial_goals:
                 last_checked_goal = 0
            else:
                 # Stelle sicher, dass wir vom *höchsten* initialen Ziel starten
                 last_checked_goal = initial_goals[-1]


            # Wende die rekursive Formel so lange an, bis das Ziel größer als die Likes ist
            # Initialisiere calculated_goal *vor* der Schleife mit dem ersten rekursiven Schritt
            calculated_goal = self.evaluate_expression_safely(recurring_expr, last_checked_goal)

            while like_count >= calculated_goal:
                 last_checked_goal = calculated_goal # Das erreichte Ziel wird zur Basis für die nächste Berechnung
                 calculated_goal = self.evaluate_expression_safely(recurring_expr, last_checked_goal)
                 # Sicherheits-Check, um Endlosschleifen zu vermeiden, falls die Formel nicht erhöht
                 if calculated_goal <= last_checked_goal:
                     server_log.error(f"Rekursive Formel '{recurring_expr}' erhöht das Ziel nicht! Abbruch.")
                     # Setze ein sinnvolles nächstes Ziel, z.B. Likes + 1 oder ein fester Wert
                     calculated_goal = like_count + 1
                     break


            current_goal = calculated_goal # Das erste Ziel, das GRÖSSER als die Likes ist


        # --- NEU: Sound-Logik beim Erreichen eines Ziels ---

        # 1. Initialisiere den Wert beim allerersten Durchlauf
        if self.previous_current_goal is None:
            self.previous_current_goal = current_goal

        # 2. Prüfe, ob sich das 'current_goal' seit dem letzten Aufruf geändert hat
        #    UND ob die aktuelle Like-Zahl größer/gleich dem *vorherigen* Ziel ist
        #    (um sicherzustellen, dass der Sound nur spielt, wenn ein Ziel *erreicht* wurde)
        if self.previous_current_goal != current_goal and like_count >= self.previous_current_goal:
            # KORREKTUR: Importiere den Service HIER, nicht am Anfang der Datei.
            # Dies löst den Zirkelbezug auf.
            from services.service_provider import audio_service_instance

            server_log.info(f"Neues Ziel {self.previous_current_goal} erreicht! Spiele Sound.")
            audio_service_instance.play_goal_sound()
            # Aktualisiere das Ziel für den nächsten Check
            self.previous_current_goal = current_goal
        # --- ENDE Sound-Logik ---

        # Stelle sicher, dass likes_needed nie negativ ist (kann passieren, wenn Ziel genau erreicht wird)
        likes_needed = max(0, int(current_goal - like_count))
        display_text = display_format.format(likes_needed=likes_needed)

        return {
            "like_count": int(like_count),
            "likes_needed": likes_needed,
            "current_goal": int(current_goal),
            "displayText": display_text
        }