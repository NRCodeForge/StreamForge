import time
import threading
import json
import logging
import os
from external.settings_manager import SettingsManager
from utils import server_log
from config import get_path

# Alle Events
from TikTokLive.events import GiftEvent, FollowEvent, ShareEvent, SubscribeEvent, CommentEvent, LikeEvent


class SubathonService:
    def __init__(self):
        self.settings_manager = SettingsManager('subathon_overlay/settings.json')

        s = self.settings_manager.load_settings()
        self.remaining_seconds = float(s.get("start_time_seconds", 3600))
        self.is_paused = True

        self.timer_logger = self._setup_timer_logger()
        self.lock = threading.Lock()
        self._hooked_to_api = False

        self.thread = threading.Thread(target=self._timer_loop, daemon=True)
        self.thread.start()

    def _setup_timer_logger(self):
        logger = logging.getLogger("TimerExclusive")
        logger.setLevel(logging.INFO)
        logger.propagate = False
        if not logger.handlers:
            h = logging.FileHandler(get_path("timer.log"), mode='a', encoding='utf-8')
            h.setFormatter(logging.Formatter('%(asctime)s - %(message)s', datefmt='%H:%M:%S'))
            logger.addHandler(h)
        return logger

    def _ensure_api_hook(self):
        if not self._hooked_to_api:
            from services.service_provider import like_service_instance
            if hasattr(like_service_instance, 'api_client') and like_service_instance.api_client:
                like_service_instance.api_client.add_listener(self.on_tiktok_event)
                self._hooked_to_api = True
                self.timer_logger.info("SYSTEM: Connected to TikTok API")

    def get_current_settings(self):
        return self.settings_manager.load_settings()

    def update_settings(self, ns):
        self.settings_manager.save_settings(ns)

    # --- CONTROL ---
    def set_paused(self, p):
        self.is_paused = p
        self.timer_logger.info(f"CONTROL: {'Pausiert' if p else 'Gestartet'}")

    def reset_timer(self):
        s = self.get_current_settings()
        val = float(s.get("start_time_seconds", 3600))
        with self.lock: self.remaining_seconds = val
        self.timer_logger.info(f"CONTROL: Reset -> {val}s")

    def _parse(self, val):
        try:
            return float(str(val).split()[0])
        except:
            return 0

    def add_time(self, seconds, reason=""):
        with self.lock: self.remaining_seconds += seconds
        self.timer_logger.info(f"ADD: +{seconds}s | {reason} | Left: {int(self.remaining_seconds)}s")

    # --- EVENTS ---
    def on_tiktok_event(self, event):
        settings = self.get_current_settings()
        added = 0
        reason = ""

        # Helper um Config zu holen (default active=False)
        def get_cfg(key):
            return settings.get(key, {"value": "0", "active": False})

        # 1. COINS
        if isinstance(event, GiftEvent):
            c = get_cfg("coins")
            if c["active"]:
                val = self._parse(c["value"])
                added = event.gift.diamond_count * val
                reason = f"Gift ({event.gift.diamond_count})"

        # 2. FOLLOW
        elif isinstance(event, FollowEvent):
            c = get_cfg("follow")
            if c["active"]:
                added = self._parse(c["value"])
                reason = "Follow"

        # 3. SHARE
        elif isinstance(event, ShareEvent):
            c = get_cfg("share")
            if c["active"]:
                added = self._parse(c["value"])
                reason = "Share"

        # 4. SUBSCRIBE
        elif isinstance(event, SubscribeEvent):
            c = get_cfg("subscribe")
            if c["active"]:
                added = self._parse(c["value"])
                reason = "Sub"

        # 5. LIKE
        elif isinstance(event, LikeEvent):
            c = get_cfg("like")
            if c["active"]:
                val = self._parse(c["value"])
                # Likes kommen in Batches, wir zählen pro Like
                count = event.count if hasattr(event, 'count') else getattr(event, 'likes', 0)
                added = val * count
                reason = f"Likes ({count})"

        # 6. CHAT
        elif isinstance(event, CommentEvent):
            c = get_cfg("chat")
            # Später: Hier Commands filtern mit 'if event.comment.startswith("!"): return'
            if c["active"]:
                added = self._parse(c["value"])
                reason = "Chat"

        if added > 0: self.add_time(added, reason)

    def handle_streamerbot_event(self, data):
        type_ = data.get("event", "").lower()
        amount = int(data.get("amount", 1))
        settings = self.get_current_settings()
        added = 0
        reason = ""

        if "sub" in type_:
            c = settings.get("twitch_sub", {"value": "0", "active": False})
            if c["active"]:
                added = self._parse(c["value"]) * amount
                reason = f"Twitch Sub x{amount}"

        elif "add" in type_:
            added = float(data.get("seconds", 0))
            reason = "Manuell"

        if added > 0: self.add_time(added, reason)

    def _timer_loop(self):
        while True:
            self._ensure_api_hook()
            if not self.is_paused and self.remaining_seconds > 0:
                with self.lock:
                    self.remaining_seconds -= 1
                    if self.remaining_seconds < 0: self.remaining_seconds = 0
            time.sleep(1)

    def get_state(self):
        h = int(self.remaining_seconds // 3600)
        m = int((self.remaining_seconds % 3600) // 60)
        s = int(self.remaining_seconds % 60)
        return {"hours": f"{h:02}", "minutes": f"{m:02}", "seconds": f"{s:02}", "total_seconds": self.remaining_seconds,
                "is_paused": self.is_paused}