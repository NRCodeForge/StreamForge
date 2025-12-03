import time
import threading
import random
import json
import os
import logging
from external.settings_manager import SettingsManager
from utils import server_log
from config import get_path

# Alle Events importieren
from TikTokLive.events import GiftEvent, FollowEvent, ShareEvent, SubscribeEvent, CommentEvent, LikeEvent


class SubathonService:
    def __init__(self):
        # 1. Logger ZUERST einrichten
        self.timer_logger = self._setup_timer_logger()
        self.timer_logger.info("--- SUBATHON SERVICE GESTARTET ---")

        self.settings_manager = SettingsManager('subathon_overlay/settings.json')

        self.timer_seconds = 0
        self.is_paused = True

        # Status-Variablen
        self.speed_multiplier = 1.0
        self.add_multiplier = 1.0
        self.is_frozen = False
        self.is_blind = False

        self._event_timers = {}
        self.current_api_ref = None
        self.gambit_queue = []

        self._load_initial_state()
        self._initialize_gambler_file()

        # Threads starten
        self.thread = threading.Thread(target=self._timer_loop, daemon=True)
        self.thread.start()

        threading.Thread(target=self._process_gambit_queue, daemon=True).start()

    def _setup_timer_logger(self):
        logger = logging.getLogger("TimerLog")
        logger.setLevel(logging.INFO)
        logger.propagate = False
        if not logger.handlers:
            try:
                path = get_path("timer.log")
                h = logging.FileHandler(path, mode='a', encoding='utf-8')
                h.setFormatter(logging.Formatter('%(asctime)s - %(message)s', datefmt='%H:%M:%S'))
                logger.addHandler(h)
            except Exception as e:
                print(f"Fehler beim Erstellen des Timer-Loggers: {e}")
        return logger

    def _ensure_api_hook(self):
        """Prüft kontinuierlich die Verbindung zur API."""
        try:
            from services.service_provider import like_service_instance
            current_api = getattr(like_service_instance, 'api_client', None)

            if current_api is not None and current_api != self.current_api_ref:
                server_log.info(f"🔌 SubathonService: Klinke mich in neue TikTok-Verbindung ein...")
                current_api.add_listener(self.on_tiktok_event)
                self.current_api_ref = current_api
        except Exception as e:
            server_log.error(f"API Hook Fehler: {e}")

    # --- EVENT VERARBEITUNG ---
    def on_tiktok_event(self, event):
        """Wird von der API aufgerufen, wenn ein Event passiert."""
        try:
            # Freezer Check: Nur Gifts kommen durch
            if self.is_frozen and not isinstance(event, GiftEvent):
                return

            settings = self.get_current_settings()
            added = 0
            reason = ""

            def get_cfg(key):
                return settings.get(key, {"value": "0", "active": False})

            def parse_val(v):
                try:
                    return float(str(v).split()[0])
                except:
                    return 0.0

            # 1. COINS (Gift)
            if isinstance(event, GiftEvent):
                c = get_cfg("coins")
                if c.get("active"):
                    val = parse_val(c["value"])
                    count = event.gift.diamond_count
                    added = count * val
                    reason = f"Gift ({count} Coins)"

            # 2. FOLLOW
            elif isinstance(event, FollowEvent):
                c = get_cfg("follow")
                if c.get("active"):
                    added = parse_val(c["value"])
                    reason = f"Follow: {event.user.unique_id}"

            # 3. SHARE
            elif isinstance(event, ShareEvent):
                c = get_cfg("share")
                if c.get("active"):
                    added = parse_val(c["value"])
                    reason = "Share"

            # 4. SUBSCRIBE
            elif isinstance(event, SubscribeEvent):
                c = get_cfg("subscribe")
                if c.get("active"):
                    added = parse_val(c["value"])
                    reason = "Abo"

            # 5. LIKE
            elif isinstance(event, LikeEvent):
                c = get_cfg("like")
                if c.get("active"):
                    val = parse_val(c["value"])
                    count = event.count
                    added = count * val
                    if added > 0: reason = f"{count} Likes"

            # 6. CHAT
            elif isinstance(event, CommentEvent):
                if not event.comment.startswith("!"):
                    c = get_cfg("chat")
                    if c.get("active"):
                        added = parse_val(c["value"])
                        reason = "Chat"

            # ZEIT HINZUFÜGEN
            if added > 0:
                self.add_time(added)
                self.timer_logger.info(f"EVENT: {reason} -> +{added}s")

        except Exception as e:
            server_log.error(f"Fehler im Timer-Handler: {e}")

    # --- TIMER LOGIK ---
    def _timer_loop(self):
        while True:
            self._ensure_api_hook()

            if not self.is_paused and not self.is_frozen and self.timer_seconds > 0:
                deduction = 1 * self.speed_multiplier
                self.timer_seconds = max(0, self.timer_seconds - deduction)

            time.sleep(1)

    # --- HELPER & LAST STAND ---
    def add_time(self, seconds):
        # 1. Last Stand Prüfung: Wenn unter 60 Sekunden -> x3
        last_stand_multiplier = 3.0 if self.timer_seconds < 60 else 1.0

        # 2. Gesamt-Multiplikator (Hype * Last Stand)
        # Beispiel: Hype (2.0) * Last Stand (3.0) = x6.0
        total_multiplier = self.add_multiplier * last_stand_multiplier

        final = seconds * total_multiplier
        self.timer_seconds += final

        # Logging für Übersicht
        log_msg = f"TIMER ADD: +{final}s (Base: {seconds}"
        if self.add_multiplier > 1.0: log_msg += f", Hype: x{self.add_multiplier}"
        if last_stand_multiplier > 1.0: log_msg += f", LAST STAND: x{last_stand_multiplier}"
        log_msg += f") -> Neu: {int(self.timer_seconds)}s"

        server_log.info(log_msg)

    # --- RESTLICHE METHODEN (Queue, Gambit, Settings...) ---
    def _process_gambit_queue(self):
        while True:
            if self.gambit_queue: next_event = self.gambit_queue[0]
            time.sleep(0.5)

    def pop_next_gambit_event(self):
        if self.gambit_queue: return self.gambit_queue.pop(0)
        return None

    def _load_initial_state(self):
        try:
            self.timer_seconds = int(self.settings_manager.load_settings().get("initial_seconds", 3600))
        except:
            self.timer_seconds = 3600

    def _initialize_gambler_file(self):
        try:
            path = get_path('gambler_overlay/active.json')
            os.makedirs(os.path.dirname(path), exist_ok=True)
            with open(path, 'w', encoding='utf-8') as f:
                json.dump({}, f)
        except:
            pass

    def get_current_settings(self):
        return self.settings_manager.load_settings()

    def update_settings(self, s):
        self.settings_manager.save_settings(s)
        server_log.info("Subathon Settings aktualisiert.")

    def set_paused(self, p):
        self.is_paused = p
        server_log.info(f"Timer Status: {'Pause' if p else 'Running'}")

    def reset_timer(self):
        self._load_initial_state()

    def _reset_event(self, a, d, k):
        setattr(self, a, d); server_log.info(f"Event {k} beendet.")

    def _start_event_timer(self, a, v, d, dur, k):
        setattr(self, a, v)
        if k in self._event_timers: self._event_timers[k].cancel()
        t = threading.Timer(dur, self._reset_event, [a, d, k])
        t.start();
        self._event_timers[k] = t

    def trigger_time_warp(self, d=60):
        self._start_event_timer('speed_multiplier', 2.0, 1.0, d, 'time_warp')

    def trigger_blackout(self, d=120):
        self._start_event_timer('is_blind', True, False, d, 'blackout')

    def trigger_freezer(self, d=180):
        self._start_event_timer('is_frozen', True, False, d, 'freezer')

    def trigger_hype_mode(self, d=300):
        self._start_event_timer('add_multiplier', 2.0, 1.0, d, 'hype_mode')

    def trigger_gambler(self):
        chamber = random.randint(1, 6)
        result_text, color = "", "#E0E0E0"

        # Bei Zeit-Adds im Gambit wirkt auch der Last Stand / Hype Multiplikator!
        if chamber == 1:
            self.add_time(300); result_text = "+ 5 MINUTEN"; color = "#00FF7F"
        elif chamber == 2:
            self.timer_seconds = max(0, self.timer_seconds - 120); result_text = "- 2 MINUTEN"; color = "#DE0B32"
        elif chamber == 3:
            self.add_time(int(self.timer_seconds * 0.25)); result_text = "+ 25% ZEIT"; color = "#00FF7F"
        elif chamber == 4:
            self.timer_seconds = max(0, self.timer_seconds - int(
                self.timer_seconds * 0.25)); result_text = "- 25% ZEIT"; color = "#DE0B32"
        elif chamber == 5:
            result_text = "👓 BRILLE AB!"; color = "#00BFFF"
        else:
            result_text = "🥔 BOHNE (GLÜCK GEHABT)"; color = "#888888"

        server_log.info(f"🎲 GAMBIT: {result_text}")
        self.gambit_queue.append({"title": "GAMBIT ROULETTE", "chamber": chamber, "result": result_text, "color": color,
                                  "timestamp": time.time()})
        return result_text

    def get_state(self):
        h, r = divmod(int(self.timer_seconds), 3600)
        m, s = divmod(r, 60)
        return {"hours": h, "minutes": m, "seconds": s, "total_seconds": int(self.timer_seconds),
                "is_paused": self.is_paused, "is_frozen": self.is_frozen, "is_blind": self.is_blind,
                "is_hype": self.add_multiplier > 1.0, "is_warp": self.speed_multiplier > 1.0}

    def handle_streamerbot_event(self, d):
        if self.is_frozen: return
        if d.get("event") == "add":
            self.add_time(int(d.get("seconds", 0)))
        elif d.get("event") == "sub":
            self.trigger_hype_mode(300)