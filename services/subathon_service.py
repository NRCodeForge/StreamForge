import time
import threading
import random
import json
import os
import logging
from external.settings_manager import SettingsManager
from utils import server_log
from config import get_path
from TikTokLive.events import GiftEvent, FollowEvent, ShareEvent, SubscribeEvent, CommentEvent, LikeEvent


class SubathonService:
    def __init__(self):
        self.timer_logger = self._setup_timer_logger()
        self.timer_logger.info("--- SUBATHON SERVICE RELOADED ---")

        self.settings_manager = SettingsManager('subathon_overlay/settings.json')

        self.timer_seconds = 0
        self.is_paused = True

        # Status
        self.speed_multiplier = 1.0
        self.add_multiplier = 1.0
        self.is_frozen = False
        self.is_blind = False

        self._event_timers = {}
        self.current_api_ref = None
        self.gambit_queue = []

        self._load_initial_state()
        self._initialize_gambler_file()

        self.thread = threading.Thread(target=self._timer_loop, daemon=True)
        self.thread.start()

        threading.Thread(target=self._process_gambit_queue, daemon=True).start()

    # --- SETUP & HELPERS ---
    def _setup_timer_logger(self):
        logger = logging.getLogger("TimerLog")
        logger.setLevel(logging.INFO)
        logger.propagate = False
        if not logger.handlers:
            try:
                h = logging.FileHandler(get_path("timer.log"), mode='a', encoding='utf-8')
                h.setFormatter(logging.Formatter('%(asctime)s - %(message)s', datefmt='%H:%M:%S'))
                logger.addHandler(h)
            except:
                pass
        return logger

    def _load_initial_state(self):
        try:
            s = self.settings_manager.load_settings()

            # FIX: Nutze denselben Key wie die GUI ("start_time_seconds")
            # Falls nicht vorhanden, Fallback auf "initial_seconds" (alt) oder 3600
            val = s.get("start_time_seconds", s.get("initial_seconds", 3600))
            self.timer_seconds = int(float(val))

            # Initiale Gambit-Werte setzen, falls leer
            if not s.get("gambit_outcomes"):
                s["gambit_outcomes"] = [
                    {"text": "+ 5 MIN", "type": "time_add", "value": 300, "color": "#00FF7F"},
                    {"text": "- 2 MIN", "type": "time_sub", "value": 120, "color": "#DE0B32"},
                    {"text": "+ 25%", "type": "time_multi_add", "value": 0.25, "color": "#00FF7F"},
                    {"text": "- 25%", "type": "time_multi_sub", "value": 0.25, "color": "#DE0B32"},
                    {"text": "BRILLE AB", "type": "text", "value": 0, "color": "#00BFFF"},
                    {"text": "BOHNE", "type": "text", "value": 0, "color": "#888888"}
                ]
                self.settings_manager.save_settings(s)

        except Exception as e:
            server_log.error(f"Fehler beim Laden der Startzeit: {e}")
            self.timer_seconds = 3600

    # --- HELPER: SICHERE ZAHLEN ---
    def _safe_float(self, value, default=0.0):
        """Wandelt Strings sicher in Floats um."""
        try:
            return float(str(value).strip().replace(',', '.'))
        except (ValueError, TypeError):
            return default

    def _safe_int(self, value, default=0):
        """Wandelt Strings sicher in Ints um."""
        try:
            return int(float(str(value).strip().replace(',', '.')))
        except (ValueError, TypeError):
            return default

    # --- HELPER: EINSTELLUNGEN HOLEN (Kombiniert neue & alte Struktur) ---
    def _get_cfg(self, settings, key):
        """
        Holt Einstellungen sicher ab.
        Unterstützt:
        1. Neue Struktur: settings[key] = {'value': 10, 'active': True}
        2. Alte Struktur (Fallback): settings[key + '_value']
        """
        # Versuch 1: Nested Object (Das ist das Ziel!)
        if key in settings and isinstance(settings[key], dict):
            return settings[key]

        # Versuch 2: Fallback auf flache Keys
        return {
            "value": settings.get(f"{key}_value", 0),
            "active": settings.get(f"{key}_active", False)
        }

    # --- API HOOK (Unverändert wichtig) ---
    def _ensure_api_hook(self):
        try:
            from services.service_provider import like_service_instance
            current_api = getattr(like_service_instance, 'api_client', None)
            if current_api is not None and current_api != self.current_api_ref:
                server_log.info(f"🔌 Subathon: Klinke mich in TikTok-API ein...")
                current_api.add_listener(self.on_tiktok_event)
                self.current_api_ref = current_api
        except:
            pass

    # --- EVENT HANDLER ---
    def on_tiktok_event(self, event):
        try:
            if self.is_frozen and not isinstance(event, GiftEvent): return

            settings = self.get_current_settings()
            added = 0
            reason = ""

            def get_cfg(key):
                return self._get_cfg(settings, key)

            if isinstance(event, GiftEvent):
                c = get_cfg("coins")
                if c.get("active"):
                    added = event.gift.diamond_count * self._safe_float(c["value"])
                    reason = f"Gift ({event.gift.diamond_count})"

            elif isinstance(event, FollowEvent):
                c = get_cfg("follow")
                if c.get("active"): added = self._safe_float(c["value"]); reason = "Follow"

            elif isinstance(event, ShareEvent):
                c = get_cfg("share")
                if c.get("active"): added = self._safe_float(c["value"]); reason = "Share"

            elif isinstance(event, SubscribeEvent):
                c = get_cfg("subscribe")
                if c.get("active"): added = self._safe_float(c["value"]); reason = "Sub"

            elif isinstance(event, LikeEvent):
                c = get_cfg("like")
                if c.get("active"):
                    added = event.count * self._safe_float(c["value"])
                    if added > 0: reason = f"{event.count} Likes"

            elif isinstance(event, CommentEvent):
                if not event.comment.startswith("!"):
                    c = get_cfg("chat")
                    if c.get("active"): added = self._safe_float(c["value"]); reason = "Chat"

            if added > 0:
                self.add_time(added)
                self.timer_logger.info(f"EVENT: {reason} -> +{added}s")

        except Exception as e:
            server_log.error(f"Event Fehler: {e}")

    # --- GAMBLER LOGIK (DYNAMISCH) ---
    def get_gambit_options(self):
        """Gibt die Liste der möglichen Ergebnisse zurück (für Frontend)."""
        s = self.get_current_settings()
        return s.get("gambit_outcomes", [])

    def trigger_gambler(self):
        outcomes = self.get_gambit_options()
        if not outcomes:
            return "Keine Optionen konfiguriert!"

        # Zufällige Wahl
        choice = random.choice(outcomes)

        result_text = choice.get("text", "???")
        rtype = choice.get("type", "text")
        rval = self._safe_float(choice.get("value", 0))
        color = choice.get("color", "#FFFFFF")

        # Effekt anwenden
        if rtype == "time_add":
            self.add_time(rval)
        elif rtype == "time_sub":
            self.timer_seconds = max(0, self.timer_seconds - rval)
        elif rtype == "time_multi_add":  # Prozent dazu
            add = int(self.timer_seconds * rval)
            self.timer_seconds += add
        elif rtype == "time_multi_sub":  # Prozent weg
            rem = int(self.timer_seconds * rval)
            self.timer_seconds = max(0, self.timer_seconds - rem)
        elif rtype == "event_freezer":
            self.trigger_freezer(int(rval))
        elif rtype == "event_warp":
            self.trigger_time_warp(int(rval))
        elif rtype == "event_blind":
            self.trigger_blackout(int(rval))
        elif rtype == "event_hype":
            self.trigger_hype_mode(int(rval))

        server_log.info(f"🎲 GAMBIT: {result_text} ({rtype})")

        # In Queue packen
        self.gambit_queue.append({
            "title": "GAMBIT ROULETTE",
            "chamber": result_text,
            "result": result_text,
            "color": color,
            "timestamp": time.time()
        })
        return result_text

    # --- RESTLICHE LOGIK (Timer Loop etc.) ---
    def _timer_loop(self):
        while True:
            self._ensure_api_hook()
            if not self.is_paused and not self.is_frozen and self.timer_seconds > 0:
                self.timer_seconds = max(0, self.timer_seconds - (1 * self.speed_multiplier))
            time.sleep(1)

    def _process_gambit_queue(self):
        while True:
            # Einfaches Polling - Queue wird von Frontend via pop_next_gambit_event geleert
            time.sleep(0.5)

    def pop_next_gambit_event(self):
        if self.gambit_queue: return self.gambit_queue.pop(0)
        return None

    def add_time(self, seconds):
        # Last Stand Logik
        ls_multi = 3.0 if self.timer_seconds < 60 else 1.0
        final = seconds * self.add_multiplier * ls_multi
        self.timer_seconds += final
        server_log.info(f"ADD: +{final:.1f}s (Base:{seconds}, Hype:x{self.add_multiplier}, LS:x{ls_multi})")

    # --- TRIGGER METHODEN FÜR EVENTS (Konfigurierbar) ---
    def _get_duration(self, key, default):
        s = self.get_current_settings()
        # FIX: Sicheres Int-Parsing für Strings aus GUI
        return self._safe_int(s.get(f"duration_{key}", default), default)

    def trigger_time_warp(self, d=None):
        dur = d if d else self._get_duration("warp", 60)
        self._start_event_timer('speed_multiplier', 2.0, 1.0, dur, 'time_warp')

    def trigger_blackout(self, d=None):
        dur = d if d else self._get_duration("blind", 120)
        self._start_event_timer('is_blind', True, False, dur, 'blackout')

    def trigger_freezer(self, d=None):
        dur = d if d else self._get_duration("freezer", 180)
        self._start_event_timer('is_frozen', True, False, dur, 'freezer')

    def trigger_hype_mode(self, d=None):
        dur = d if d else self._get_duration("hype", 300)
        self._start_event_timer('add_multiplier', 2.0, 1.0, dur, 'hype_mode')

    # Standard Helpers
    def _initialize_gambler_file(self):
        try:
            os.makedirs(get_path('gambler_overlay'), exist_ok=True);
        except:
            pass

    def get_current_settings(self):
        return self.settings_manager.load_settings()

    def update_settings(self, s):
        self.settings_manager.save_settings(s);
        server_log.info("Settings saved.")

    def set_paused(self, p):
        self.is_paused = p

    def reset_timer(self):
        self._load_initial_state()

    def _reset_event(self, a, d, k):
        setattr(self, a, d);
        server_log.info(f"Event {k} end.")

    def _start_event_timer(self, a, v, d, dur, k):
        setattr(self, a, v)
        if k in self._event_timers: self._event_timers[k].cancel()
        t = threading.Timer(dur, self._reset_event, [a, d, k])
        t.start();
        self._event_timers[k] = t

    def get_state(self):
        h, r = divmod(int(self.timer_seconds), 3600);
        m, s = divmod(r, 60)
        return {"hours": h, "minutes": m, "seconds": s, "total_seconds": int(self.timer_seconds),
                "is_paused": self.is_paused, "is_frozen": self.is_frozen, "is_blind": self.is_blind,
                "is_hype": self.add_multiplier > 1.0, "is_warp": self.speed_multiplier > 1.0}

    def handle_streamerbot_event(self, d):
        if self.is_frozen: return
        if d.get("event") == "add":
            self.add_time(int(d.get("seconds", 0)))
        elif d.get("event") == "sub":
            self.trigger_hype_mode()

    # --- TWITCH EVENTS (KORRIGIERT & VEREINHEITLICHT) ---
    def on_twitch_message(self, username):
        """Wird bei jeder Chat-Nachricht aufgerufen."""
        s = self.get_current_settings()
        cfg = self._get_cfg(s, "twitch_msg")

        # Check ob aktiv
        if not cfg.get("active", False): return

        val = self._safe_float(cfg.get("value", 0))
        if val > 0:
            self.add_time(val)
            self.timer_logger.info(f"TWITCH: Msg ({username}) -> +{val}s")

    def on_twitch_sub(self, username, is_gift=False):
        """Wird bei Sub oder Gift-Sub aufgerufen."""
        s = self.get_current_settings()

        if is_gift:
            # Gift Sub
            cfg = self._get_cfg(s, "twitch_gift")
            if cfg.get("active", False):
                val = self._safe_float(cfg.get("value", 0))
                self.add_time(val)
                self.timer_logger.info(f"TWITCH: Gift Sub ({username}) -> +{val}s")
        else:
            # Normaler Sub (Prime, Tier 1-3)
            cfg = self._get_cfg(s, "twitch_sub")
            if cfg.get("active", False):
                val = self._safe_float(cfg.get("value", 0))
                self.add_time(val)
                self.timer_logger.info(f"TWITCH: Sub ({username}) -> +{val}s")

    def on_twitch_bits(self, username, amount):
        """Wird bei Bits aufgerufen."""
        s = self.get_current_settings()
        cfg = self._get_cfg(s, "twitch_bits")

        if cfg.get("active", False):
            factor = self._safe_float(cfg.get("value", 0))  # Zeit pro 1 Bit
            total_time = amount * factor
            if total_time > 0:
                self.add_time(total_time)
                self.timer_logger.info(f"TWITCH: {amount} Bits ({username}) -> +{total_time}s")

    def get_time_string(self):
        # Helper für Overlay
        m, s = divmod(int(self.timer_seconds), 60)
        h, m = divmod(m, 60)
        return f"{h:02d}:{m:02d}:{s:02d}"