import logging
from TikTokLive import TikTokLiveClient
from TikTokLive.events import ConnectEvent, LikeEvent
from TikTokLive.client.web.web_settings import WebDefaults

# --- KONFIGURATION ---
USER_NAME = "@dbdstation"  # <--- HIER USERNAME EINTRAGEN
EULER_KEY = "euler_ODBmYTc0ZWZjMmU0NmIyNzU4YjM3MmI4YzUwYmMxZWYwNjllNmVhZjI1MjBiN2ViMjE1YzRh"

# Logging aktivieren
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("TiktokDebug")

# Key setzen
WebDefaults.tiktok_sign_api_key = EULER_KEY

client = TikTokLiveClient(unique_id=USER_NAME)


@client.on(ConnectEvent)
async def on_connect(event: ConnectEvent):
    logger.info(f"Verbunden mit {event.unique_id}!")

    # Diagnose 1: Was steht in den Room Info? (Startwert)
    if client.room_info:
        logger.info("--- ROOM INFO DIAGNOSE ---")
        # Wir geben alle Keys aus, die nach 'like' klingen
        keys = client.room_info.keys()
        like_keys = [k for k in keys if 'like' in k.lower()]
        logger.info(f"Gefundene Like-Keys in RoomInfo: {like_keys}")
        for k in like_keys:
            logger.info(f" -> {k}: {client.room_info[k]}")
    else:
        logger.error("❌ client.room_info ist LEER! (Startwert fehlt)")


@client.on(LikeEvent)
async def on_like(event: LikeEvent):
    logger.info("--- LIKE EVENT DIAGNOSE ---")

    # Diagnose 2: Welche Attribute hat das Event wirklich?
    # Wir filtern interne Attribute (_) raus
    attributes = [d for d in dir(event) if not d.startswith('_')]

    # Wir suchen nach allem was wie 'total' oder 'count' aussieht
    relevante_attribute = [a for a in attributes if 'total' in a.lower() or 'like' in a.lower() or 'count' in a.lower()]

    logger.info(f"VERFÜGBARE DATEN IM EVENT: {relevante_attribute}")

    # Werte dieser Attribute ausgeben
    for attr in relevante_attribute:
        try:
            val = getattr(event, attr)
            if isinstance(val, (int, str)) or val is None:
                logger.info(f" -> {attr}: {val}")
        except:
            pass

    # Stoppt nach dem ersten Like, damit du das Log lesen kannst
    logger.info("Diagnose fertig. Du kannst das Skript stoppen.")


if __name__ == "__main__":
    # fetch_room_info ist wichtig für den Startwert!
    client.run(fetch_room_info=True)