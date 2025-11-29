import threading
import time
import asyncio
import logging
from typing import Optional, Callable, List, Dict

# TikTokLive Importe
from TikTokLive import TikTokLiveClient
from TikTokLive.events import (
    ConnectEvent, LikeEvent, DisconnectEvent, LiveEndEvent,
    GiftEvent, FollowEvent, ShareEvent, SubscribeEvent, CommentEvent
)

# EulerStream Konfiguration
from TikTokLive.client.web.web_settings import WebDefaults

# --- KONFIGURATION EULERSTREAM ---
# Dein Key (euler_...)
EULER_API_KEY = "euler_ODBmYTc0ZWZjMmU0NmIyNzU4YjM3MmI4YzUwYmMxZWYwNjllNmVhZjI1MjBiN2ViMjE1YzRh"
WebDefaults.tiktok_sign_api_key = EULER_API_KEY

# Logging Setup
logging.basicConfig(level=logging.INFO)
server_log = logging.getLogger("TikTokAPI")


class TikTokLive_API:
    def __init__(self, unique_id: str):
        self.unique_id = unique_id
        self.client: Optional[TikTokLiveClient] = None

        # --- ZÄHLER ---
        self.current_likes = 0  # Gesamt-Likes im Raum (synchronisiert mit Server)
        self.user_likes: Dict[str, int] = {}  # Likes pro User (für dein Leaderboard)

        self.is_connected = False
        self.running = False
        self.thread = None
        self._lock = threading.Lock()

        self.listeners: List[Callable[[any], None]] = []

    def add_listener(self, callback: Callable[[any], None]):
        """Registriert einen Listener für Events."""
        self.listeners.append(callback)

    def _notify_listeners(self, event):
        """Leitet Events an alle Listener weiter."""
        for callback in self.listeners:
            try:
                callback(event)
            except Exception as e:
                server_log.error(f"Fehler im Event-Listener: {e}")

    def start(self):
        if self.running: return
        self.running = True
        self.thread = threading.Thread(target=self._run_loop, daemon=True)
        self.thread.start()
        server_log.info(f"API gestartet für: @{self.unique_id} (EulerStream aktiv)")

    def stop(self):
        self.running = False
        if self.client:
            try:
                loop = getattr(self.client, '_asyncio_loop', None) or asyncio.get_event_loop()
                if loop and loop.is_running():
                    asyncio.run_coroutine_threadsafe(self.client.disconnect(), loop)
                else:
                    self.client.stop()
            except Exception as e:
                server_log.error(f"Hinweis beim Stoppen: {e}")

    def _run_loop(self):
        while self.running:
            try:
                self.client = TikTokLiveClient(unique_id=self.unique_id)

                # Event-Listener registrieren
                self.client.add_listener(ConnectEvent, self.on_connect)
                self.client.add_listener(DisconnectEvent, self.on_disconnect)
                self.client.add_listener(LiveEndEvent, self.on_live_end)
                self.client.add_listener(LikeEvent, self.on_like)
                self.client.add_listener(GiftEvent, self.on_gift)
                self.client.add_listener(FollowEvent, self.on_follow)
                self.client.add_listener(ShareEvent, self.on_share)
                self.client.add_listener(SubscribeEvent, self.on_subscribe)
                self.client.add_listener(CommentEvent, self.on_comment)

                server_log.info(f"Verbinde zu TikTok Live @{self.unique_id}...")

                # Room Info für Start-Likes holen
                self.client.run(fetch_room_info=True)

            except Exception as e:
                if self.running:
                    server_log.error(f"TikTok Live Verbindung unterbrochen: {e}")
                self.is_connected = False
                time.sleep(10)

            if self.running and not self.is_connected:
                time.sleep(2)

    # --- Event Handlers ---

    async def on_connect(self, event: ConnectEvent):
        self.is_connected = True
        server_log.info(f"✅ Verbunden mit @{self.unique_id}!")

        # Initialisierung beim Start (versucht verschiedene Keys, sicher ist sicher)
        with self._lock:
            if self.client.room_info:
                r_info = self.client.room_info
                start_likes = r_info.get('like_count', 0) or r_info.get('total_likes', 0) or r_info.get('likes_count',
                                                                                                        0)

                if int(start_likes) > self.current_likes:
                    self.current_likes = int(start_likes)
                    server_log.info(f"Start-Likes gesetzt auf: {self.current_likes}")

    async def on_disconnect(self, event: DisconnectEvent):
        self.is_connected = False
        server_log.warning("⚠️ Verbindung getrennt.")

    async def on_live_end(self, event: LiveEndEvent):
        self.is_connected = False
        server_log.info("Stream beendet.")

    # --- WICHTIG: Korrigierte Like Logik ---

    async def on_like(self, event: LikeEvent):
        user_id = event.user.unique_id

        # 'count' ist die Anzahl der Likes in DIESEM Klick (Batch)
        batch_count = event.count

        with self._lock:
            # 1. Zuerst lokal hochzählen (falls Server-Total mal fehlt)
            self.current_likes += batch_count

            # 2. Synchronisation mit 'event.total' (das Feld aus deiner Diagnose!)
            if hasattr(event, 'total'):
                server_total = event.total
                # Wir nehmen immer den höheren Wert (Server gewinnt meistens)
                if server_total >= self.current_likes:
                    self.current_likes = server_total

            # 3. User-spezifisches Tracking (für dein Like-Board)
            if user_id not in self.user_likes:
                self.user_likes[user_id] = 0
            self.user_likes[user_id] += batch_count

            # 4. Daten an das Event anhängen für deine Listener
            event.custom_room_total = self.current_likes  # Gesamt-Likes im Stream
            event.custom_user_total = self.user_likes[user_id]  # Likes von diesem User

        # Weiterleitung an deine App
        self._notify_listeners(event)

    async def on_gift(self, event: GiftEvent):
        # Nur wenn Streak zu Ende oder nicht streakable -> Event feuern
        if event.gift.streakable and not event.repeat_end:
            return
        self._notify_listeners(event)

    async def on_follow(self, event: FollowEvent):
        self._notify_listeners(event)

    async def on_share(self, event: ShareEvent):
        self._notify_listeners(event)

    async def on_subscribe(self, event: SubscribeEvent):
        self._notify_listeners(event)

    async def on_comment(self, event: CommentEvent):
        self._notify_listeners(event)

    def get_current_likes(self) -> int:
        with self._lock:
            return self.current_likes