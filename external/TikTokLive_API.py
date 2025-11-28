import threading
import time
import asyncio
from typing import Optional, Callable, List

from TikTokLive import TikTokLiveClient
from TikTokLive.events import (
    ConnectEvent, LikeEvent, DisconnectEvent, LiveEndEvent,
    GiftEvent, FollowEvent, ShareEvent, SubscribeEvent, CommentEvent
)
from utils import server_log


class TikTokLive_API:
    def __init__(self, unique_id: str):
        self.unique_id = unique_id
        self.client: Optional[TikTokLiveClient] = None

        self.current_likes = 0
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
        server_log.info(f"TikTok Live API Thread gestartet für: @{self.unique_id}")

    def stop(self):
        self.running = False
        if self.client:
            try:
                if hasattr(self.client, 'stop'):
                    self.client.stop()
                elif hasattr(self.client, 'disconnect'):
                    asyncio.run_coroutine_threadsafe(self.client.disconnect(), self.client.loop)
            except Exception as e:
                server_log.error(f"Hinweis beim Stoppen: {e}")

    def _run_loop(self):
        while self.running:
            try:
                self.client = TikTokLiveClient(unique_id=self.unique_id)

                # Standard Connection Events
                self.client.on(ConnectEvent)(self.on_connect)
                self.client.on(DisconnectEvent)(self.on_disconnect)
                self.client.on(LiveEndEvent)(self.on_live_end)

                # Interaktions-Events
                self.client.on(LikeEvent)(self.on_like)
                self.client.on(GiftEvent)(self.on_gift)
                self.client.on(FollowEvent)(self.on_follow)
                self.client.on(ShareEvent)(self.on_share)
                self.client.on(SubscribeEvent)(self.on_subscribe)
                self.client.on(CommentEvent)(self.on_comment)  # NEU: Chat

                server_log.info(f"Verbinde zu TikTok Live @{self.unique_id}...")
                self.client.run()

            except Exception as e:
                if self.running: server_log.error(f"TikTok Live Verbindung unterbrochen: {e}")
                self.is_connected = False

            if self.running: time.sleep(5)

    # --- Event Handlers ---

    async def on_connect(self, event: ConnectEvent):
        self.is_connected = True
        server_log.info(f"✅ Verbunden mit @{self.unique_id}!")
        try:
            if hasattr(self.client, 'retrieve_room_info'):
                await self.client.retrieve_room_info()

            with self._lock:
                if self.client.room_info:
                    if isinstance(self.client.room_info, dict):
                        likes = int(self.client.room_info.get('like_count', 0))
                    else:
                        likes = getattr(self.client.room_info, 'like_count', 0) or getattr(self.client.room_info,
                                                                                           'likes_count', 0)

                    if likes > 0: self.current_likes = likes
        except Exception:
            pass

    async def on_disconnect(self, event: DisconnectEvent):
        self.is_connected = False
        server_log.warning("⚠️ Verbindung getrennt.")

    async def on_live_end(self, event: LiveEndEvent):
        self.is_connected = False
        server_log.info("Stream beendet.")

    # --- Events Weiterleitung ---

    async def on_like(self, event: LikeEvent):
        with self._lock:
            batch = event.count if hasattr(event, 'count') else getattr(event, 'likes', 0)
            self.current_likes += batch
            if hasattr(event, 'totalLikes') and event.totalLikes > self.current_likes:
                self.current_likes = event.totalLikes
        self._notify_listeners(event)

    async def on_gift(self, event: GiftEvent):
        if event.gift.streak_end or not event.gift.streakable:
            self._notify_listeners(event)

    async def on_follow(self, event: FollowEvent):
        self._notify_listeners(event)

    async def on_share(self, event: ShareEvent):
        self._notify_listeners(event)

    async def on_subscribe(self, event: SubscribeEvent):
        self._notify_listeners(event)

    async def on_comment(self, event: CommentEvent):
        # NEU: Chat Nachrichten
        self._notify_listeners(event)

    def get_current_likes(self) -> int:
        with self._lock: return self.current_likes