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

# EulerStream Konfiguration
from TikTokLive.client.web.web_settings import WebDefaults

# --- KONFIGURATION EULERSTREAM ---
EULER_API_KEY = "euler_ODBmYTc0ZWZjMmU0NmIyNzU4YjM3MmI4YzUwYmMxZWYwNjllNmVhZjI1MjBiN2ViMjE1YzRh"
WebDefaults.tiktok_sign_api_key = EULER_API_KEY

# --- KONFIGURATION SPEICHERN ---
SAVE_INTERVAL = 30  # Alle 30 Sekunden speichern
JSON_FILENAME = "like_daten.json"  # Datei für die Daten
LOG_FILENAME = "tiktok_live.log"  # Datei für das Protokoll

# --- LOGGING SETUP (Erweitert) ---
# Schreibt jetzt Zeitstempel und speichert alles zusätzlich in eine Datei
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
    handlers=[
        logging.FileHandler(LOG_FILENAME, encoding='utf-8'),  # Speichert in Datei
        logging.StreamHandler()  # Zeigt in Konsole
    ]
)
server_log = logging.getLogger("TikTokAPI")


class TikTokLive_API:
    def __init__(self, unique_id: str):
        self.unique_id = unique_id
        self.client: Optional[TikTokLiveClient] = None

        # --- ZÄHLER ---
        self.current_likes = 0
        self.user_likes: Dict[str, int] = {}

        # --- STATUS & THREADS ---
        self.is_connected = False
        self.running = False

        self.api_thread = None  # Thread für TikTok Verbindung
        self.timer_thread = None  # Thread für Auto-Save
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

    # --- START / STOP LOGIK ---

    def start(self):
        if self.running: return
        self.running = True

        # 1. API Thread starten (Verbindung zu TikTok)
        self.api_thread = threading.Thread(target=self._run_loop, daemon=True)
        self.api_thread.start()

        # 2. Timer Thread starten (Automatisches Speichern)
        self.timer_thread = threading.Thread(target=self._run_save_timer, daemon=True)
        self.timer_thread.start()

        server_log.info(f"🚀 API gestartet für: @{self.unique_id} (EulerStream aktiv)")
        server_log.info(f"💾 Auto-Save aktiv: Alle {SAVE_INTERVAL} Sekunden in '{JSON_FILENAME}'")

    def stop(self):
        server_log.info("🛑 Stoppe System...")
        self.running = False

        # Ein letztes Mal speichern beim Stoppen
        self.save_data_to_file()

        if self.client:
            try:
                loop = getattr(self.client, '_asyncio_loop', None) or asyncio.get_event_loop()
                if loop and loop.is_running():
                    asyncio.run_coroutine_threadsafe(self.client.disconnect(), loop)
                else:
                    self.client.stop()
            except Exception as e:
                server_log.error(f"Hinweis beim Stoppen: {e}")

    # --- DATEN SPEICHERN (NEU) ---

    def save_data_to_file(self):
        """Speichert Likes und User-Daten in eine JSON Datei"""
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

            # Loggt den Speichervorgang in Datei und Konsole
            server_log.info(f"💾 [TIMER] Gespeichert. Total: {self.current_likes} | User: {len(self.user_likes)}")

        except Exception as e:
            server_log.error(f"❌ Fehler beim Speichern: {e}")

    def _run_save_timer(self):
        """Hintergrund-Loop für das automatische Speichern"""
        while self.running:
            time.sleep(SAVE_INTERVAL)
            if self.running:
                self.save_data_to_file()

    # --- HAUPT LOOP ---

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

        # Initialisierung beim Start
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
        server_log.info("🏁 Stream beendet.")
        self.save_data_to_file()  # Sofort speichern bei Ende

    # --- Like Logik (Deine Version mit 'total') ---

    async def on_like(self, event: LikeEvent):
        user_id = event.user.unique_id
        batch_count = event.count

        with self._lock:
            # 1. Zuerst lokal hochzählen
            self.current_likes += batch_count

            # 2. Synchronisation mit 'event.total'
            if hasattr(event, 'total'):
                server_total = event.total
                if server_total >= self.current_likes:
                    self.current_likes = server_total

            # 3. User-spezifisches Tracking
            if user_id not in self.user_likes:
                self.user_likes[user_id] = 0
            self.user_likes[user_id] += batch_count

            # 4. Daten an das Event anhängen
            event.custom_room_total = self.current_likes
            event.custom_user_total = self.user_likes[user_id]

        self._notify_listeners(event)

    async def on_gift(self, event: GiftEvent):
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