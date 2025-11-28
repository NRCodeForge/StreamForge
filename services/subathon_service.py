import time
import threading
import json
import logging
import os
from external.settings_manager import SettingsManager
from utils import server_log
from config import get_path

# Event Typen
from TikTokLive.events import GiftEvent, FollowEvent, ShareEvent, SubscribeEvent


class SubathonService:
    def __init__(self):
        self.settings_manager = SettingsManager('subathon_overlay/settings.json')

        # Lade Startzeit aus Settings (Default: 3600s / 1h)
        settings = self.settings_manager.load_settings()
        start_val = settings.get("start_time_seconds", 3600)

        self.remaining_seconds = float(start_val)
        self.is_paused = True

        # Logger Setup
        self.timer_logger = self._setup_timer_logger()

        self.lock = threading.Lock()

        # WICHTIG: Variable initialisieren BEVOR der Thread startet!
        self._hooked_to_api = False

        # Thread starten
        self.thread = threading.Thread(target=self._timer_loop, daemon=True)
        self.thread.start()

    def _setup_timer_logger(self):
        """Erstellt einen isolierten Logger, der NUR in timer.log schreibt."""
        logger = logging.getLogger("TimerExclusive")
        logger.setLevel(logging.INFO)
        logger.propagate = False  # Verhindert, dass es in der Konsole/Main-Log landet

        if not logger.handlers:
            log_path = get_path("timer.log")
            handler = logging.FileHandler(log_path, mode='a', encoding='utf-8')
            formatter = logging.Formatter('%(asctime)s - %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
            handler.setFormatter(formatter)
            logger.addHandler(handler)

        return logger

    def _ensure_api_hook(self):
        """Verbindet sich mit der TikTok API. Löst Zirkelbezug durch lokalen Import."""
        if not self._hooked_to_api:
            # FIX: Import hier drinnen, damit service_provider zuerst laden kann
            from services.service_provider import like_service_instance

            # Prüfen ob API Client existiert und läuft
            if hasattr(like_service_instance, 'api_client') and like_service_instance.api_client:
                like_service_instance.api_client.add_listener(self.on_tiktok_event)
                self._hooked_to_api = True
                self.timer_logger.info("SYSTEM: Verbunden mit TikTok API.")

    def get_current_settings(self):
        return self.settings_manager.load_settings()

    def update_settings(self, new_settings):
        self.settings_manager.save_settings(new_settings)

    # --- CONTROL METHODS ---
    def set_paused(self, paused: bool):
        self.is_paused = paused
        status = "Pausiert" if paused else "Gestartet"
        self.timer_logger.info(f"CONTROL: Timer {status}")

    def reset_timer(self):
        """Setzt den Timer auf den Wert in den Settings zurück."""
        settings = self.get_current_settings()
        start_val = float(settings.get("start_time_seconds", 3600))
        with self.lock:
            self.remaining_seconds = start_val
        self.timer_logger.info(f"CONTROL: Reset auf {start_val}s")

    def _parse_time_value(self, value_str):
        try:
            parts = str(value_str).split()
            amount = float(parts[0])
            # Prüfe Einheiten falls vorhanden
            if len(parts) > 1:
                unit = parts[1].lower()
                if 'minute' in unit: return amount * 60
                if 'hour' in unit: return amount * 3600
            return amount
        except:
            return 0

    def add_time(self, seconds, reason="Unbekannt"):
        """Fügt Zeit hinzu und schreibt in den Timer-Log."""
        with self.lock:
            self.remaining_seconds += seconds
            new_time_str = self._format_time(self.remaining_seconds)

        # Logging
        self.timer_logger.info(f"ADD: +{seconds}s | Grund: {reason} | Neu: {new_time_str}")

    def _format_time(self, total_seconds):
        h = int(total_seconds // 3600)
        m = int((total_seconds % 3600) // 60)
        s = int(total_seconds % 60)
        return f"{h:02}:{m:02}:{s:02}"

    def on_tiktok_event(self, event):
        """Reagiert auf TikTok Events."""
        settings = self.get_current_settings()
        added_time = 0
        reason = ""

        # 1. COINS (Gifts)
        if isinstance(event, GiftEvent):
            cfg = settings.get("coins", {})
            if cfg.get("active"):
                coins = event.gift.diamond_count
                time_per_coin = self._parse_time_value(cfg.get("value", "0"))
                added_time = coins * time_per_coin
                reason = f"TikTok Gift: {event.gift.name} ({coins} Coins)"

        # 2. FOLLOW
        elif isinstance(event, FollowEvent):
            cfg = settings.get("follow", {})
            if cfg.get("active"):
                added_time = self._parse_time_value(cfg.get("value", "0"))
                reason = f"TikTok Follow: {event.user.unique_id}"

        # 3. SHARE
        elif isinstance(event, ShareEvent):
            cfg = settings.get("share", {})
            if cfg.get("active"):
                added_time = self._parse_time_value(cfg.get("value", "0"))
                reason = f"TikTok Share: {event.user.unique_id}"

        # 4. SUBSCRIBE
        elif isinstance(event, SubscribeEvent):
            cfg = settings.get("subscribe", {})
            if cfg.get("active"):
                added_time = self._parse_time_value(cfg.get("value", "0"))
                reason = f"TikTok Sub: {event.user.unique_id}"

        if added_time > 0:
            self.add_time(added_time, reason)

    def handle_streamerbot_event(self, data):
        """Reagiert auf Streamer.bot (Twitch) Events."""
        event_type = data.get("event", "").lower()
        amount = int(data.get("amount", 1))

        settings = self.get_current_settings()
        added_time = 0
        reason = ""

        if "sub" in event_type:
            cfg = settings.get("twitch_sub", {})
            if cfg.get("active"):
                time_per_sub = self._parse_time_value(cfg.get("value", "0"))
                added_time = time_per_sub * amount
                reason = f"Twitch Sub (x{amount})"

        elif "add" in event_type:
            seconds = float(data.get("seconds", 0))
            added_time = seconds
            reason = "Manuell (Streamer.bot)"

        if added_time > 0:
            self.add_time(added_time, reason)

    def _timer_loop(self):
        """Zählt die Zeit herunter."""
        while True:
            self._ensure_api_hook()  # Verbindung prüfen

            if not self.is_paused and self.remaining_seconds > 0:
                with self.lock:
                    self.remaining_seconds -= 1
                    if self.remaining_seconds < 0: self.remaining_seconds = 0

            time.sleep(1)

    def get_state(self):
        hours = int(self.remaining_seconds // 3600)
        minutes = int((self.remaining_seconds % 3600) // 60)
        seconds = int(self.remaining_seconds % 60)

        return {
            "hours": f"{hours:02}",
            "minutes": f"{minutes:02}",
            "seconds": f"{seconds:02}",
            "total_seconds": self.remaining_seconds,
            "is_paused": self.is_paused
        }