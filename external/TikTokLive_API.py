import threading
import time
import asyncio
import logging
import json
import datetime
from typing import Optional, Callable, List, Dict

# TikTokLive Importe
from TikTokLive import TikTokLiveClient
from TikTokLive.events import (
    ConnectEvent, LikeEvent, DisconnectEvent, LiveEndEvent,
    GiftEvent, FollowEvent, ShareEvent, SubscribeEvent, CommentEvent
)
from TikTokLive.client.web.web_settings import WebDefaults




# EulerStream Key
EULER_API_KEY = "euler_ODBmYTc0ZWZjMmU0NmIyNzU4YjM3MmI4YzUwYmMxZWYwNjllNmVhZjI1MjBiN2ViMjE1YzRh"

# --- GLOBALE SETTINGS ---
WebDefaults.tiktok_sign_api_key = EULER_API_KEY

SAVE_INTERVAL = 30
JSON_FILENAME = "like_daten.json"
LOG_FILENAME = "tiktok_live.log"

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
    handlers=[logging.FileHandler(LOG_FILENAME, encoding='utf-8'), logging.StreamHandler()]
)
server_log = logging.getLogger("TikTokAPI")


class TikTokLive_API:
    def __init__(self, unique_id: str):
        self.unique_id = unique_id
        self.client: Optional[TikTokLiveClient] = None
        self.current_likes = 0
        self.user_likes: Dict[str, int] = {}
        self.is_connected = False
        self.running = False
        self.api_thread = None
        self.timer_thread = None
        self._lock = threading.Lock()
        self.listeners: List[Callable[[any], None]] = []

    def add_listener(self, callback: Callable[[any], None]):
        self.listeners.append(callback)

    def _notify_listeners(self, event):
        def _run_callback(cb, evt):
            try:
                cb(evt)
            except Exception as e:
                server_log.error(f"Fehler im Event-Listener: {e}")

        for callback in self.listeners:
            threading.Thread(target=_run_callback, args=(callback, event), daemon=True).start()

    def start(self):
        if self.running: return
        self.running = True
        self.api_thread = threading.Thread(target=self._run_connection_loop, daemon=True, name="TikTokConnectionLoop")
        self.api_thread.start()
        self.timer_thread = threading.Thread(target=self._run_save_timer, daemon=True, name="TikTokSaveTimer")
        self.timer_thread.start()
        server_log.info(f"🚀 API gestartet für: @{self.unique_id}")

    def stop(self):
        server_log.info("🛑 Stoppe System...")
        self.running = False
        self.save_data_to_file()
        if self.client:
            try:
                loop = getattr(self.client, '_asyncio_loop', None) or asyncio.get_event_loop()
                if loop and loop.is_running():
                    asyncio.run_coroutine_threadsafe(self.client.disconnect(), loop)
                else:
                    self.client.stop()
            except Exception:
                pass

    def save_data_to_file(self):
        try:
            with self._lock:
                data = {
                    "timestamp": str(datetime.datetime.now()),
                    "streamer": self.unique_id,
                    "total_room_likes": self.current_likes,
                    "user_leaderboard": self.user_likes
                }
            with open(JSON_FILENAME, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=4)
            server_log.info(f"💾 [TIMER] Gespeichert. Likes: {self.current_likes}")
        except Exception as e:
            server_log.error(f"Speicherfehler: {e}")

    def _run_save_timer(self):
        while self.running:
            time.sleep(SAVE_INTERVAL)
            if self.running: self.save_data_to_file()

    def _run_connection_loop(self):
        retry_delay = 3
        while self.running:
            try:
                self.client = TikTokLiveClient(unique_id=self.unique_id)



                # Events
                self.client.add_listener(ConnectEvent, self.on_connect)
                self.client.add_listener(DisconnectEvent, self.on_disconnect)
                self.client.add_listener(LiveEndEvent, self.on_live_end)
                self.client.add_listener(LikeEvent, self.on_like)
                self.client.add_listener(GiftEvent, self.on_gift)
                self.client.add_listener(FollowEvent, self.on_follow)
                self.client.add_listener(ShareEvent, self.on_share)
                self.client.add_listener(SubscribeEvent, self.on_subscribe)
                self.client.add_listener(CommentEvent, self.on_comment)

                server_log.info(f"🔄 [LOOP] Verbinde zu @{self.unique_id} (Workaround aktiv)...")

                # --- FIX: fetch_room_info=False ---
                # Das verhindert den Absturz bei Age-Restricted Streams
                self.client.run(fetch_room_info=False)

            except Exception as e:
                self.is_connected = False
                if self.running:
                    server_log.warning(f"⚠️ Verbindung getrennt ({e}). Reconnect in {retry_delay}s...")
                    time.sleep(retry_delay)
                else:
                    break

    # --- HANDLERS ---
    async def on_connect(self, event: ConnectEvent):
        self.is_connected = True
        server_log.info(f"✅ Verbunden mit @{self.unique_id}!")
        # Hinweis: Da fetch_room_info=False ist, haben wir hier evtl. keine Start-Likes.
        # Das ist aber besser als gar keine Verbindung!

    async def on_disconnect(self, event: DisconnectEvent):
        self.is_connected = False
        server_log.warning("⚠️ Getrennt.")

    async def on_live_end(self, event: LiveEndEvent):
        self.is_connected = False
        server_log.info("🏁 Stream Ende.")
        self.save_data_to_file()

    async def on_like(self, event: LikeEvent):
        uid = event.user.unique_id
        count = event.count
        with self._lock:
            self.current_likes += count
            # Event.total ist evtl. nicht verfügbar bei fetch_room_info=False
            if hasattr(event, 'total') and event.total >= self.current_likes:
                self.current_likes = event.total
            if uid not in self.user_likes: self.user_likes[uid] = 0
            self.user_likes[uid] += count
            event.custom_room_total = self.current_likes
            event.custom_user_total = self.user_likes[uid]
        self._notify_listeners(event)

    async def on_gift(self, event: GiftEvent):
        if event.gift.streakable and not event.repeat_end: return
        self._notify_listeners(event)

    async def on_follow(self, event: FollowEvent):
        self._notify_listeners(event)

    async def on_share(self, event: ShareEvent):
        self._notify_listeners(event)

    async def on_subscribe(self, event: SubscribeEvent):
        self._notify_listeners(event)
        try:
            from services.service_provider import subathon_service_instance
            subathon_service_instance.trigger_hype_mode(300)
        except:
            pass

    async def on_comment(self, event: CommentEvent):
        self._notify_listeners(event)
        from services.service_provider import wish_service_instance, subathon_service_instance
        try:
            d = event.user_info
            name = getattr(d, "nick_name", None) or getattr(d, "nickname", None) or getattr(d, "unique_id", "Unknown")
            txt = event.comment.strip()
            server_log.info(f"💬 {name}: {txt}")

            if txt.lower().startswith("!place"):
                wish_service_instance.check_user_place(name)
        except Exception as e:
            server_log.error(f"Comment Error: {e}")

    def get_current_likes(self) -> int:
        with self._lock: return self.current_likes