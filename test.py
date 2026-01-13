import os
import sys
import io
import json
import asyncio
from datetime import datetime
from TikTokLive import TikTokLiveClient
from TikTokLive.client.web.web_settings import WebDefaults

# --- SYSTEM SETUP ---
os.environ['WHITELIST_AUTHENTICATED_SESSION_ID_HOST'] = 'tiktok.eulerstream.com'

if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', line_buffering=True)
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

# --- KONFIGURATION ---
UNIQUE_ID = "kai8594_yt"
EULER_KEY = "euler_ODBmYTc0ZWZjMmU0NmIyNzU4YjM3MmI4YzUwYmMxZWYwNjllNmVhZjI1MjBiN2ViMjE1YzRh"
SESSION_ID = "f7b226fdfbd1537165e6650b8fdb9897"
SAMPLE_FILE = "event_samples.json"

WebDefaults.tiktok_sign_api_key = EULER_KEY


def now(): return datetime.now().strftime("%H:%M:%S")


# --- DYNAMISCHER IMPORT DER EVENTS ---
# Wir importieren nur, was wirklich da ist, um Abstürze zu verhindern
import TikTokLive.events as events

event_map = {}

potential_events = [
    'ConnectEvent', 'CommentEvent', 'GiftEvent', 'LikeEvent',
    'RankUpdateEvent', 'WeeklyRankRewardEvent', 'MemberEvent',
    'FollowEvent', 'ShareEvent', 'GoalUpdateEvent', 'RoomViewerCountEvent'
]

for e_name in potential_events:
    if hasattr(events, e_name):
        event_map[e_name] = getattr(events, e_name)


class ScalperV31:
    def __init__(self, target_id):
        self.client = TikTokLiveClient(unique_id=target_id)
        self.client.web.cookies.set("sessionid", SESSION_ID)
        self.captured_types = set()

    def start_scalping(self):
        print(f"[{now()}] 🔍 Suche nach Events: {', '.join(event_map.keys())}")

        # Registriere alle gefundenen Events
        for name, cls in event_map.items():
            @self.client.on(cls)
            async def on_event(event, event_name=name):
                if event_name not in self.captured_types:
                    self.captured_types.add(event_name)
                    self.save_event(event_name, event)

    def save_event(self, name, event):
        try:
            # Wir holen uns das __dict__ und machen es JSON-sicher
            raw_dict = {str(k): str(v) for k, v in event.__dict__.items()}

            output = {
                "timestamp": now(),
                "event": name,
                "dict_data": raw_dict
            }

            with open(SAMPLE_FILE, "a", encoding="utf-8") as f:
                f.write(json.dumps(output, ensure_ascii=False) + "\n")

            print(f"\n[⭐] NEUES PAKET: {name} gespeichert!")
        except Exception as e:
            print(f"Fehler beim Speichern von {name}: {e}")

    def run(self):
        self.start_scalping()
        print(f"[{now()}] 🚀 Scalper läuft auf @{UNIQUE_ID}...")
        # Bypass-Start
        self.client.run(fetch_room_info=False, fetch_live_check=False)


if __name__ == "__main__":
    # Datei leeren für neuen Scan
    with open(SAMPLE_FILE, "w") as f: pass

    bot = ScalperV31(UNIQUE_ID)
    bot.run()