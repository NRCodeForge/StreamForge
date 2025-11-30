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
# Dein Key gegen "Device Blocked" Fehler
EULER_API_KEY = "euler_ODBmYTc0ZWZjMmU0NmIyNzU4YjM3MmI4YzUwYmMxZWYwNjllNmVhZjI1MjBiN2ViMjE1YzRh"
WebDefaults.tiktok_sign_api_key = EULER_API_KEY

# --- KONFIGURATION SPEICHERN ---
SAVE_INTERVAL = 30
JSON_FILENAME = "like_daten.json"
LOG_FILENAME = "tiktok_live.log"

# --- LOGGING SETUP ---
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
    handlers=[
        logging.FileHandler(LOG_FILENAME, encoding='utf-8'),
        logging.StreamHandler()
    ]
)
server_log = logging.getLogger("TikTokAPI")


class TikTokLive_API:
    def __init__(self, unique_id: str):
        self.unique_id = unique_id
        self.client: Optional[TikTokLiveClient] = None

        # --- ZÄHLER & DATEN ---
        self.current_likes = 0
        self.user_likes: Dict[str, int] = {}

        # --- STATUS & THREADS ---
        self.is_connected = False
        self.running = False  # Kontroll-Flag statt "True"

        self.api_thread = None
        self.timer_thread = None
        self._lock = threading.Lock()

        self.listeners: List[Callable[[any], None]] = []

    def add_listener(self, callback: Callable[[any], None]):
        """Registriert externe Funktionen, die bei Events aufgerufen werden."""
        self.listeners.append(callback)

    def _notify_listeners(self, event):
        """Leitet Events an alle registrierten Listener weiter."""

        # Wir starten für jeden Listener einen kleinen Thread, damit der Main-Loop nicht blockiert
        def _run_callback(cb, evt):
            try:
                cb(evt)
            except Exception as e:
                server_log.error(f"Fehler im Event-Listener Callback: {e}")

        for callback in self.listeners:
            # Echtes "Fire-and-Forget" Multithreading für Events
            threading.Thread(target=_run_callback, args=(callback, event), daemon=True).start()

    # --- START / STOP ---

    def start(self):
        if self.running:
            return

        server_log.info(f"🚀 Starte System für: @{self.unique_id}")
        self.running = True

        # 1. API Thread (Die Verbindungsschleife)
        self.api_thread = threading.Thread(target=self._run_connection_loop, daemon=True, name="TikTokConnectionLoop")
        self.api_thread.start()

        # 2. Timer Thread (Auto-Save)
        self.timer_thread = threading.Thread(target=self._run_save_timer, daemon=True, name="TikTokSaveTimer")
        self.timer_thread.start()

    def stop(self):
        server_log.info("🛑 Stoppe System...")
        self.running = False  # Beendet die Schleifen
        self.save_data_to_file()

        if self.client:
            try:
                # Versuch eines sauberen Disconnects
                loop = getattr(self.client, '_asyncio_loop', None)
                if loop and loop.is_running():
                    asyncio.run_coroutine_threadsafe(self.client.disconnect(), loop)
                else:
                    # Fallback
                    pass
            except Exception:
                pass

    # --- DATEN SPEICHERN ---

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
            # server_log.info("💾 Daten gespeichert.")
        except Exception as e:
            server_log.error(f"❌ Speicherfehler: {e}")

    def _run_save_timer(self):
        while self.running:
            time.sleep(SAVE_INTERVAL)
            if self.running:
                self.save_data_to_file()

    # --- HAUPTVERBINDUNGS-LOOP (ROBUST) ---

    def _run_connection_loop(self):
        """
        Verbindet sich immer wieder neu, wenn die Verbindung abbricht oder 'Offline' gemeldet wird.
        """
        retry_delay = 3  # Sekunden warten vor Neustart

        while self.running:
            try:
                # 1. Client frisch instanziieren
                self.client = TikTokLiveClient(unique_id=self.unique_id)

                # 2. Events binden
                self.client.add_listener(ConnectEvent, self.on_connect)
                self.client.add_listener(DisconnectEvent, self.on_disconnect)
                self.client.add_listener(LiveEndEvent, self.on_live_end)
                self.client.add_listener(LikeEvent, self.on_like)
                self.client.add_listener(GiftEvent, self.on_gift)
                self.client.add_listener(FollowEvent, self.on_follow)
                self.client.add_listener(ShareEvent, self.on_share)
                self.client.add_listener(SubscribeEvent, self.on_subscribe)
                self.client.add_listener(CommentEvent, self.on_comment)

                server_log.info(f"🔄 [LOOP] Verbinde zu @{self.unique_id}...")

                # 3. Starten (Blockiert, bis Fehler/Ende)
                # fetch_room_info=True ist wichtig für Start-Likes
                self.client.run(fetch_room_info=True)

            except Exception as e:
                # HIER fangen wir "User Offline", "Not Found" etc. ab
                self.is_connected = False

                if self.running:
                    # Logge den Fehler, aber mache weiter!
                    server_log.warning(f"⚠️ Verbindung getrennt/fehlerhaft ({e}). Reconnect in {retry_delay}s...")
                    time.sleep(retry_delay)
                else:
                    server_log.info("ℹ️ Loop wird beendet.")
                    break

    # --- EVENT HANDLER ---

    async def on_connect(self, event: ConnectEvent):
        self.is_connected = True
        server_log.info(f"✅ VERBUNDEN mit @{self.unique_id} (RoomID: {self.client.room_id})")

        # Start-Likes übernehmen
        with self._lock:
            if self.client.room_info:
                info = self.client.room_info
                # Verschiedene Keys probieren
                start = info.get('like_count') or info.get('total_likes') or info.get('likes_count') or 0
                if int(start) > self.current_likes:
                    self.current_likes = int(start)
                    server_log.info(f"📊 Start-Likes erkannt: {self.current_likes}")

    async def on_disconnect(self, event: DisconnectEvent):
        self.is_connected = False
        # Keine Panik, der Loop oben fängt das und verbindet neu!

    async def on_live_end(self, event: LiveEndEvent):
        self.is_connected = False
        server_log.info("🏁 Stream wurde regulär beendet.")
        self.save_data_to_file()

    async def on_like(self, event: LikeEvent):
        user_id = event.user.unique_id
        count = event.count

        with self._lock:
            self.current_likes += count

            # Sync mit Server-Total falls verfügbar
            if hasattr(event, 'total') and event.total > self.current_likes:
                self.current_likes = event.total

            # User-Leaderboard
            if user_id not in self.user_likes:
                self.user_likes[user_id] = 0
            self.user_likes[user_id] += count

            # Daten für Overlay mitsenden
            event.custom_room_total = self.current_likes
            event.custom_user_total = self.user_likes[user_id]

        self._notify_listeners(event)

    async def on_gift(self, event: GiftEvent):
        if event.gift.streakable and not event.repeat_end:
            return
        self._notify_listeners(event)

    # --- KOMMENTARE & !PLACE ---
    async def on_comment(self, event: CommentEvent):
        self._notify_listeners(event)

        # Lazy Import
        from services.service_provider import wish_service_instance, subathon_service_instance

        try:
            # 1. Namen sicher auslesen (Bugfix für user.nickname Fehler)
            u_info = event.user_info
            user_name = getattr(u_info, "nick_name", None) or \
                        getattr(u_info, "nickname", None) or \
                        getattr(u_info, "unique_id", "Unbekannt")

            text = event.comment.strip()
            # 2. Timer Update (Optional)
            SECONDS_PER_COMMENT = 0
            if SECONDS_PER_COMMENT > 0:
                try:
                    subathon_service_instance.add_time(SECONDS_PER_COMMENT)
                except:
                    pass

            # 3. !place Check
            if text.lower().startswith("!place"):
                server_log.info(f"📩 !place Befehl von {user_name}")
                wish_service_instance.check_user_place(user_name)


        except Exception as e:
            server_log.error(f"Kommentar-Fehler: {e}")

    # Standard Listener
    async def on_follow(self, e):
        self._notify_listeners(e)

    async def on_share(self, e):
        self._notify_listeners(e)

    async def on_subscribe(self, event: SubscribeEvent):
        # 1. Standard Listener
        self._notify_listeners(event)

        # 2. HYPE MODE Trigger (Event 5)
        # Import hier, um Zirkelbezug zu vermeiden
        from services.service_provider import subathon_service_instance

        server_log.info(f"🌟 Neuer Sub von {event.user.unique_id}! Starte Hype-Mode.")
        # Startet Hype-Mode für 5 Minuten (300 Sekunden)
        subathon_service_instance.trigger_hype_mode(300)

    def get_current_likes(self) -> int:
        with self._lock:
            return self.current_likes