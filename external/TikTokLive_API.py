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
    GiftEvent, FollowEvent, ShareEvent, CommentEvent, EnvelopeEvent, EnvelopePortalEvent
)
from TikTokLive.events.custom_events import SuperFanEvent
from TikTokLive.client.web.web_settings import WebDefaults

# Standard Fallback Key (falls der User keinen eingibt)
DEFAULT_EULER_KEY = "euler_ODBmYTc0ZWZjMmU0NmIyNzU4YjM3MmI4YzUwYmMxZWYwNjllNmVhZjI1MjBiN2ViMjE1YzRh"

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
    def __init__(self, unique_id: str, euler_key: str = None):
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

        # --- KEY SETZEN ---
        # Nutze den übergebenen Key, sonst den Default-Key
        final_key = euler_key if euler_key and euler_key.strip() else DEFAULT_EULER_KEY

        # Setze den Key global für WebDefaults (wichtig für Signierung)
        WebDefaults.tiktok_sign_api_key = final_key

        # Logge (maskiert), welcher Key genutzt wird
        key_masked = final_key[:10] + "..." if final_key else "None"
        server_log.info(f"🔑 Nutze Euler-Key: {key_masked}")

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
                self.client.add_listener(SuperFanEvent, self.on_subscribe)
                self.client.add_listener(CommentEvent, self.on_comment)
                self.client.add_listener(EnvelopeEvent, self.on_treasure)
                self.client.add_listener(EnvelopePortalEvent, self.on_portal)

                server_log.info(f"🔄 [LOOP] Verbinde zu @{self.unique_id} (Workaround aktiv)...")

                # --- FIX: fetch_room_info=False ---
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

    async def on_disconnect(self, event: DisconnectEvent):
        self.is_connected = False
        server_log.warning("⚠️ Getrennt.")

    async def on_live_end(self, event: LiveEndEvent):
        self.is_connected = False
        server_log.info("🏁 Stream Ende.")
        self.save_data_to_file()

    # In external/TikTokLive_API.py

    async def on_like(self, event: LikeEvent):
        with self._lock:
            old_total = self.current_likes

            # 1. Neues Total ermitteln (entweder aus dem Event-Total oder inkrementell)
            # TikTok sendet im LikeEvent oft ein 'total' Feld mit den gesamten Raum-Likes.
            new_total = getattr(event, 'total', old_total + event.count)

            # 2. Sicherheitsscheck: Das Total darf nicht sinken (TikTok-Glitches verhindern)
            if new_total < old_total:
                new_total = old_total + event.count

            # 3. Die tatsächliche Differenz im Raum berechnen
            diff = new_total - old_total
            self.current_likes = new_total

            # 4. Differenz im Event-Objekt "schmuggeln", damit Listener sie lesen können
            event.calculated_diff = diff

            # User-Statistik (optional, bleibt meist auf dem Klick-Count basierend sinnvoll)
            uid = event.user.unique_id
            if uid not in self.user_likes: self.user_likes[uid] = 0
            self.user_likes[uid] += event.count

            event.custom_room_total = self.current_likes
            event.custom_user_total = self.user_likes[uid]

        self._notify_listeners(event)

    async def on_gift(self, event: GiftEvent):
        if event.gift.streakable and not event.repeat_end: return
        self._notify_listeners(event)

    async def on_follow(self, event: FollowEvent):
        self._notify_listeners(event)

    def emit_to_overlay(self, event_name, data):
        # Hier nutzen wir deine bestehende web_api_instance, um das Signal via Socket.io zu senden
        from presentation.web_api import socketio
        socketio.emit(event_name, data)

    async def on_treasure(self, event: EnvelopeEvent):
        try:
            # 1. FILTER: Ignoriere Events mit Status "HIDE"
            # Diese enthalten keine visuellen Infos für den Stream
            if "HIDE" in str(event.display):
                return

            info = event.envelope_info
            if not info:
                return

            # 2. Nicknamen extrahieren (Erster Versuch über Message-Pieces, sonst Fallback)
            try:
                nickname = event.base_message.display_text.pieces[0].user_value.user.nick_name
            except:
                nickname = info.send_user_name

            if not nickname:
                return

            # 3. Logik basierend auf Business Type
            # Type 19 = Superfan | Type 1 = Treasure
            b_type = getattr(info, 'business_type', 0)
            mode = ""
            prompt = ""

            if b_type == 19:
                # --- SUPERFAN LOGIK ---
                mode = "superfan"
                # Anzahl steht laut Log im people_count
                count = getattr(info, 'people_count', 1)
                prompt = f"{nickname} hat {count} Super Fan Box(en) verschenkt!"

            elif b_type == 1:
                # --- TREASURE LOGIK ---
                mode = "treasure"
                coins = getattr(info, 'diamond_count', 0)
                # Nur Truhen mit Inhalt anzeigen
                if coins <= 0:
                    return
                prompt = f"{nickname} hat eine Truhe mit {coins} Münzen geworfen.\n Immer schön Danke sagen :)"

            else:
                # Andere Envelope-Typen ignorieren
                return

            # 4. Daten-Paket für das Web-Overlay schnüren
            data = {
                "mode": mode,
                "prompt": prompt
            }

            # Sende an Socket.io Overlay
            self.emit_to_overlay("loot_event", data)
            server_log.info(f"💰 {mode.upper()} Event: {nickname} (Count/Coins: {getattr(info, 'people_count', coins)})")

        except Exception as e:
            server_log.error(f"Fehler im on_treasure Handler: {e}")

    async def on_portal(self, event: EnvelopePortalEvent):
        print(event.__dict__)
        print("Portal")



    async def on_share(self, event: ShareEvent):
        self._notify_listeners(event)

    async def on_subscribe(self, event: SuperFanEvent):
        try:
            from services.service_provider import subathon_service_instance
            # 1. Hype Mode aktivieren (wie bisher)
            self._notify_listeners(event)

        except Exception as e:
            server_log.error(f"Fehler beim Verarbeiten des Subs im Subathon-Service: {e}")

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