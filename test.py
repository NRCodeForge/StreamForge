import sys
import time
import asyncio  # Importiert für die Hintergrund-Synchronisierung
from TikTokLive import TikTokLiveClient
from TikTokLive.events import ConnectEvent, LikeEvent, DisconnectEvent
from typing import Dict

# --- Ziel-Benutzer ---
TARGET_USER = "@dbdstation"
SYNC_INTERVAL_SECONDS = 30  # Alle 30 Sek. den offiziellen Zähler abrufen

# --- Leaderboard-Speicher ---
like_leaderboard: Dict[str, int] = {}
total_likes_on_connect: int = 0
# Diese Variable wird nun im Hintergrund durch die API aktualisiert
current_total_likes_from_api: int = 0

# --- Client-Instanz ---
client: TikTokLiveClient = TikTokLiveClient(unique_id=TARGET_USER)


async def sync_total_likes():
    """
    Diese Funktion läuft im Hintergrund (als "Task")
    und ruft alle X Sekunden den echten Like-Zähler von der API ab.
    """
    global current_total_likes_from_api

    while client.connected:
        try:
            # Rufe die Rauminformationen von der API ab
            await client.fetch_room_info()

            # Aktualisiere unsere "verlustfreie" Zählvariable
            if client.room_info and hasattr(client.room_info, 'like_count'):
                current_total_likes_from_api = client.room_info.like_count

        except Exception as e:
            print(f"[Sync-Fehler] Konnte Gesamt-Likes nicht abrufen: {e}")

        # Warte das Intervall ab, bevor die Schleife erneut läuft
        await asyncio.sleep(SYNC_INTERVAL_SECONDS)


@client.on(ConnectEvent)
async def on_connect(event: ConnectEvent):
    """
    Wird ausgelöst, wenn die Verbindung zum Livestream erfolgreich hergestellt wurde.
    """
    global total_likes_on_connect, current_total_likes_from_api
    print(f"Erfolgreich verbunden mit @{event.unique_id} (Room ID: {client.room_id})")

    try:
        # Lese den Startwert der Likes
        if client.room_info and hasattr(client.room_info, 'like_count'):
            total_likes_on_connect = client.room_info.like_count
            current_total_likes_from_api = total_likes_on_connect
            print(f"Info: Stream hatte beim Verbinden {total_likes_on_connect} Likes.")
        else:
            print("Warnung: 'like_count' konnte nicht gelesen werden. Starte bei 0.")
            total_likes_on_connect = 0
            current_total_likes_from_api = 0

    except Exception as e:
        print(f"Fehler beim Lesen der 'room_info': {e}")
        total_likes_on_connect = 0
        current_total_likes_from_api = 0

    # Leaderboard für neue Events zurücksetzen
    like_leaderboard.clear()

    # --- STARTE DEN HINTERGRUND-SYNC ---
    # Erstellt einen neuen "Task", der parallel zum Event-Listener läuft
    asyncio.create_task(sync_total_likes())

    print(f"Starte Like-Leaderboard... Sync läuft alle {SYNC_INTERVAL_SECONDS} Sek.")
    print_leaderboard()


@client.on(LikeEvent)
async def on_like(event: LikeEvent):
    """
    Wird für jeden (verlustbehafteten) Like-Batch ausgelöst.
    """
    try:
        username = event.user.nickname
    except Exception:
        username = "Unbekannter_Benutzer"

    likes_in_this_event = event.count

    # Zähler im Leaderboard (nur für NEUE Events) hochzählen
    current_likes = like_leaderboard.get(username, 0)
    like_leaderboard[username] = current_likes + likes_in_this_event

    # Leaderboard in der Konsole ausgeben
    print_leaderboard()


@client.on(DisconnectEvent)
async def on_disconnect(event: DisconnectEvent):
    """
    Wird ausgelöst, wenn die Verbindung getrennt wird.
    """
    print("Verbindung getrennt. Der Sync-Task wird beendet.")
    # Der 'sync_total_likes'-Task stoppt automatisch, da 'client.connected' False wird.


def print_leaderboard():
    """
    Helferfunktion: Sortiert das Leaderboard und gibt alles formatiert aus.
    """
    # Konsole leeren (ANSI-Escape-Code)
    print("\033[H\033[J")

    # Neue Likes (basierend auf Events, verlustbehaftet)
    new_likes_via_events = sum(like_leaderboard.values())

    # Berechnete Summe (verlustbehaftet)
    calculated_total = total_likes_on_connect + new_likes_via_events

    # Diskrepanz (Verlust) berechnen
    discrepancy = current_total_likes_from_api - calculated_total

    print(f"--- LIVE LIKE-LEADERBOARD FÜR @{TARGET_USER} ---")
    print("-------------------------------------------------")
    print(f"Likes beim Verbinden:   {total_likes_on_connect}")
    print(f"Neue Likes (Events):    {new_likes_via_events}")
    print("-------------------------------------------------")
    print(f"GESAMTE LIKES (API):    {current_total_likes_from_api}  <-- (Verlustfrei)")
    print(f"Berechnete Summe:       {calculated_total}  <-- (Verlustbehaftet)")
    print(f"Diskrepanz (Verlust):   {discrepancy if discrepancy > 0 else 0}")
    print("-------------------------------------------------")
    print("--- Top 10 Spender (Basierend auf Events) ---")

    sorted_leaderboard = sorted(like_leaderboard.items(), key=lambda item: item[1], reverse=True)

    if not sorted_leaderboard:
        print(" Bisher keine neuen Likes...")

    for i, (user, likes) in enumerate(sorted_leaderboard[:10]):
        print(f" #{i + 1}: {user}  ->  {likes} Likes")

    print("-------------------------------------------------")
    print(f"Nächster API-Sync in max. {SYNC_INTERVAL_SECONDS} Sekunden")

    sys.stdout.flush()


if __name__ == '__main__':
    print(f"Versuche, dauerhafte Verbindung zu @{TARGET_USER} aufzubauen...")

    while True:
        try:
            client.run()

            print("Stream beendet oder Verbindung verloren.")

        except ConnectionRefusedError:
            print("[Con refuse] Verbindung abgelehnt. Server könnte down sein.")
        except Exception as e:
            print(f"Ein Fehler ist aufgetreten: {e}")
            print("Möglicher Grund: Der Stream ist (noch) nicht live.")

        print("Versuche in 10 Sekunden erneut...")
        time.sleep(10)