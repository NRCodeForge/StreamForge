import time
import threading
import random
import logging
from external.settings_manager import SettingsManager
from utils import server_log


class SubathonService:
    def __init__(self):
        self.settings_manager = SettingsManager('subathon_overlay/settings.json')

        self.timer_seconds = 0
        self.is_paused = True

        # Status-Variablen für Events
        self.speed_multiplier = 1.0
        self.add_multiplier = 1.0
        self.is_frozen = False
        self.is_blind = False

        self._event_timers = {}

        # --- GAMBIT QUEUE (Nur im Speicher) ---
        self.gambit_queue = []

        self._load_initial_state()

        # Timer Thread starten
        self.thread = threading.Thread(target=self._run_timer, daemon=True)
        self.thread.start()

    # --- NEU: API METHODE FÜR DAS OVERLAY ---
    def pop_next_gambit_event(self):
        """
        Wird vom Overlay aufgerufen.
        Gibt das nächste Event zurück und löscht es aus der Warteschlange.
        """
        if self.gambit_queue:
            return self.gambit_queue.pop(0)
        return None  # Nichts zu tun

    # --- GAMBLER LOGIK ---
    def trigger_gambler(self):
        """Fügt ein neues Gambit-Event zur Warteschlange hinzu."""
        chamber = random.randint(1, 6)
        result_text = ""
        color = "#E0E0E0"

        # Timer-Effekte sofort anwenden
        if chamber == 1:
            self.add_time(300)
            result_text = "+ 5 MINUTEN"
            color = "#00FF7F"  # Grün
        elif chamber == 2:
            remove_seconds = 120
            self.timer_seconds = max(0, self.timer_seconds - remove_seconds)
            result_text = "- 2 MINUTEN"
            color = "#DE0B32"  # Rot
        elif chamber == 3:
            add_seconds = int(self.timer_seconds * 0.25)
            self.timer_seconds += add_seconds
            result_text = f"+ 25% ZEIT ({add_seconds}s)"
            color = "#00FF7F"
        elif chamber == 4:
            remove_seconds = int(self.timer_seconds * 0.25)
            self.timer_seconds = max(0, self.timer_seconds - remove_seconds)
            result_text = f"- 25% ZEIT (-{remove_seconds}s)"
            color = "#DE0B32"
        elif chamber == 5:
            result_text = "👓 BRILLE AB!"
            color = "#00BFFF"  # Blau
        else:
            result_text = "🥔 BOHNE (GLÜCK GEHABT)"
            color = "#888888"  # Grau

        server_log.info(f"🎲 GAMBIT QUEUED: Kammer {chamber} -> {result_text}")

        # Datenpaket für die Queue erstellen
        event_data = {
            "title": "GAMBIT ROULETTE",
            "chamber": chamber,
            "result": result_text,
            "color": color,
            "timestamp": time.time()
        }

        # Einfach an die Liste anhängen
        self.gambit_queue.append(event_data)
        return result_text

    # --- STANDARD LOGIK (Wie zuvor) ---
    def get_current_settings(self):
        return self.settings_manager.load_settings()

    def update_settings(self, s):
        self.settings_manager.save_settings(s)

    def _load_initial_state(self):
        try:
            self.timer_seconds = int(self.settings_manager.load_settings().get("initial_seconds", 3600))
        except:
            self.timer_seconds = 3600

    def _run_timer(self):
        while True:
            if not self.is_paused and not self.is_frozen and self.timer_seconds > 0:
                self.timer_seconds = max(0, self.timer_seconds - (1 * self.speed_multiplier))
            time.sleep(1)

    def add_time(self, seconds):
        final = seconds * self.add_multiplier
        self.timer_seconds += final
        server_log.info(f"Timer +{final}s (Hype: x{self.add_multiplier})")

    def _reset_event(self, attr, val, key):
        setattr(self, attr, val)
        server_log.info(f"Event {key} beendet.")

    def _start_event_timer(self, attr, val, default, duration, key):
        setattr(self, attr, val)
        if key in self._event_timers: self._event_timers[key].cancel()
        t = threading.Timer(duration, self._reset_event, [attr, default, key])
        t.start();
        self._event_timers[key] = t

    def trigger_time_warp(self, d=60):
        self._start_event_timer('speed_multiplier', 2.0, 1.0, d, 'time_warp')

    def trigger_blackout(self, d=120):
        self._start_event_timer('is_blind', True, False, d, 'blackout')

    def trigger_freezer(self, d=180):
        self._start_event_timer('is_frozen', True, False, d, 'freezer')

    def trigger_hype_mode(self, d=300):
        self._start_event_timer('add_multiplier', 2.0, 1.0, d, 'hype_mode')

    def set_paused(self, p):
        self.is_paused = p

    def reset_timer(self):
        self._load_initial_state()

    def get_state(self):
        h, r = divmod(int(self.timer_seconds), 3600)
        m, s = divmod(r, 60)
        return {"hours": h, "minutes": m, "seconds": s, "total_seconds": int(self.timer_seconds),
                "is_paused": self.is_paused, "is_frozen": self.is_frozen, "is_blind": self.is_blind,
                "is_hype": self.add_multiplier > 1.0, "is_warp": self.speed_multiplier > 1.0}

    def handle_streamerbot_event(self, d):
        if d.get("event") == "add":
            self.add_time(int(d.get("seconds", 0)))
        elif d.get("event") == "sub":
            self.trigger_hype_mode(300)