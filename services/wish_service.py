import json
import os
import time
import threading
from database.wish_repository import WishRepository
from utils import wishes_log
from config import get_path


class WishService:
    """Verwaltet die Geschäftslogik für Killerwünsche."""

    def __init__(self):
        self.repository = WishRepository()
        self.offset_counter = 0
        self._initialize_overlay_file()

    def _initialize_overlay_file(self):
        """Erstellt die place_overlay/active.json (im Root)."""
        try:
            path = get_path('place_overlay/active.json')
            os.makedirs(os.path.dirname(path), exist_ok=True)
            self._write_place_overlay({})
        except Exception as e:
            wishes_log.error(f"Fehler beim Initialisieren des Place-Overlays: {e}")

    def get_current_wishes(self):
        return self.repository.get_wishes(self.offset_counter)

    def advance_offset(self):
        self.repository.delete_oldest_wish()
        total = self.repository.count_total_wishes()
        if self.offset_counter >= total:
            self.offset_counter = 0
        return self.offset_counter

    def add_new_wish(self, wunsch, user_name):
        self.repository.add_wish(wunsch, user_name)
        wishes_log.info(f'Neuer Wunsch von {user_name}: {wunsch}')

    def reset_wishes(self):
        self.repository.delete_all_wishes()
        self.offset_counter = 0

    # --- !place Logik MIT AUTO-RESET ---
    def check_user_place(self, user_name):
        """Ermittelt Platz, schreibt Overlay und löscht es nach 8s."""
        all_users = self.repository.get_all_user_names()

        try:
            user_lower = user_name.lower()
            all_users_lower = [u.lower() for u in all_users]
            place = all_users_lower.index(user_lower) + 1
            display_name = all_users[place - 1]  # Original Name aus DB
        except ValueError:
            place = -1
            display_name = user_name

        wishes_log.info(f"CHECK PLACE für '{user_name}': Platz {place}")

        if place > 0:
            overlay_data = {
                "user_name": display_name,
                "place": place,
                "timestamp": time.time()
            }
            self._write_place_overlay(overlay_data)

            # Timer starten: Nach 8 Sekunden Datei leeren
            threading.Timer(8.0, self._clear_overlay).start()
            return place
        else:
            return None

    def _clear_overlay(self):
        """Leert die active.json, damit das Overlay verschwindet."""
        self._write_place_overlay({})

    def _write_place_overlay(self, data):
        try:
            path = get_path('place_overlay/active.json')
            with open(path, 'w', encoding='utf-8') as f:
                json.dump(data, f)
        except Exception as e:
            wishes_log.error(f"Fehler beim Schreiben des Place-Overlays: {e}")