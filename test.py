import logging
from TikTokLive import TikTokLiveClient
from TikTokLive.events import ConnectEvent, CommentEvent, DisconnectEvent
from TikTokLive.client.web.web_settings import WebDefaults

# ---------------------------------------------------------
# KONFIGURATION
# ---------------------------------------------------------
TIKTOK_USERNAME = "dbdstation"

# DEIN EulerStream Key (wichtig gegen 'DEVICE_BLOCKED')
EULER_KEY = "euler_ODBmYTc0ZWZjMmU0NmIyNzU4YjM3MmI4YzUwYmMxZWYwNjllNmVhZjI1MjBiN2ViMjE1YzRh"

# ---------------------------------------------------------

# Logging einstellen (zeigt Infos in der Konsole)
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("TestScript")

# EulerStream aktivieren
WebDefaults.tiktok_sign_api_key = EULER_KEY

# Client erstellen
client: TikTokLiveClient = TikTokLiveClient(unique_id=TIKTOK_USERNAME)


@client.on(ConnectEvent)
async def on_connect(event: ConnectEvent):
    logger.info(f"✅ Verbunden mit @{event.unique_id} (Room ID: {client.room_id})")
    logger.info("Warte auf Kommentare... (Schreibe etwas in den Chat)")


@client.on(CommentEvent)
async def on_comment(event: CommentEvent):
    try:
        # BUGFIX: Direktzugriff auf user_info um den TypeError zu vermeiden
        user_data = event.user_info

        # Versuche verschiedene Namen-Felder
        name = getattr(user_data, "nick_name", None) or \
               getattr(user_data, "nickname", None) or \
               getattr(user_data, "unique_id", "Unbekannt")

        text = event.comment

        print(f"💬 {name}: {text}")
        if text.lower().startswith("!place"):
            print(True)


    except Exception as e:
        logger.error(f"Fehler beim Lesen des Kommentars: {e}")


@client.on(DisconnectEvent)
async def on_disconnect(event: DisconnectEvent):
    logger.warning("❌ Verbindung getrennt.")


if __name__ == '__main__':
    logger.info(f"Start mit EulerStream Key... Verbinde zu {TIKTOK_USERNAME}")
    while True:
        try:
            client.run(fetch_room_info=True)
        except Exception as e:
            logger.error(f"Kritischer Fehler: {e}")