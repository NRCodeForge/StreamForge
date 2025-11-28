import threading
import time
import asyncio
from typing import Optional

# Bibliothek von isaackogan/TikTokLive
from TikTokLive import TikTokLiveClient
from TikTokLive.events import ConnectEvent, LikeEvent, DisconnectEvent, LiveEndEvent
from utils import server_log


class TikTokLive_API:
    def __init__(self, unique_id: str):
        self.unique_id = unique_id
        self.client: Optional[TikTokLiveClient] = None

        # Daten-Speicher
        self.current_likes = 0
        self.is_connected = False

        # Threading-Kontrolle
        self.running = False
        self.thread = None
        self._lock = threading.Lock()

    def start(self):
        """Startet den Client in einem separaten Thread."""
        if self.running:
            return

        self.running = True
        self.thread = threading.Thread(target=self._run_loop, daemon=True)
        self.thread.start()
        server_log.info(f"TikTok Live API Thread gestartet für: @{self.unique_id}")

    def stop(self):
        """Stoppt den Client sauber."""
        self.running = False
        if self.client:
            try:
                # Versuche verschiedene Methoden zum Beenden
                if hasattr(self.client, 'stop'):
                    self.client.stop()
                elif hasattr(self.client, 'disconnect'):
                    asyncio.run_coroutine_threadsafe(self.client.disconnect(), self.client.loop)
            except Exception as e:
                server_log.error(f"Hinweis beim Stoppen: {e}")

    def _run_loop(self):
        """Die interne Loop, die versucht, die Verbindung aufrechtzuerhalten."""
        while self.running:
            try:
                # KORREKTUR: Parameter 'fetch_room_info_on_connect' entfernt!
                self.client = TikTokLiveClient(unique_id=self.unique_id)

                # Events registrieren
                self.client.on(ConnectEvent)(self.on_connect)
                self.client.on(LikeEvent)(self.on_like)
                self.client.on(DisconnectEvent)(self.on_disconnect)
                self.client.on(LiveEndEvent)(self.on_live_end)

                server_log.info(f"Verbinde zu TikTok Live @{self.unique_id}...")
                self.client.run()

            except Exception as e:
                if self.running:
                    server_log.error(f"TikTok Live Verbindung unterbrochen: {e}")
                self.is_connected = False

            # Kurze Pause vor Reconnect
            if self.running:
                time.sleep(5)

    # --- Events ---

    async def on_connect(self, event: ConnectEvent):
        self.is_connected = True
        server_log.info(f"✅ Verbunden mit @{self.unique_id}!")

        # Hole die initialen Likes manuell
        try:
            # Versuche retrieve_room_info aufzurufen, falls vorhanden
            if hasattr(self.client, 'retrieve_room_info'):
                await self.client.retrieve_room_info()

            with self._lock:
                server_likes = 0
                if self.client.room_info:
                    # Sicherer Zugriff auf Like-Count
                    if isinstance(self.client.room_info, dict):
                        server_likes = int(self.client.room_info.get('like_count', 0))
                    else:
                        # Objekt-Zugriff
                        server_likes = getattr(self.client.room_info, 'like_count', 0)
                        if server_likes == 0:
                            # Manchmal heißt das Attribut anders
                            server_likes = getattr(self.client.room_info, 'likes_count', 0)

                    if server_likes > 0:
                        self.current_likes = server_likes
                        server_log.info(f"Start-Likes geladen: {self.current_likes}")
        except Exception as e:
            server_log.warning(f"Konnte Start-Likes nicht laden (nicht kritisch): {e}")

    async def on_disconnect(self, event: DisconnectEvent):
        self.is_connected = False
        server_log.warning("⚠️ Verbindung zu TikTok getrennt.")

    async def on_live_end(self, event: LiveEndEvent):
        self.is_connected = False
        server_log.info("Stream wurde beendet.")

    async def on_like(self, event: LikeEvent):
        with self._lock:
            # Dynamisches Auslesen der Likes aus dem Event
            batch_likes = 0
            if hasattr(event, 'count'):
                batch_likes = event.count
            elif hasattr(event, 'likes'):
                batch_likes = event.likes

            self.current_likes += batch_likes

            # Optional: Abgleich mit Gesamt-Likes falls das Event diese liefert
            if hasattr(event, 'totalLikes') and event.totalLikes > self.current_likes:
                self.current_likes = event.totalLikes

    # --- Public Accessor ---

    def get_current_likes(self) -> int:
        with self._lock:
            return self.current_likes