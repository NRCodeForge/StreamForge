# StreamForge/services/wish_service.py

# KORREKTUR: Verwende absolute Importe
from database.wish_repository import WishRepository
from utils import wishes_log


class WishService:
    """Verwaltet die Geschäftslogik und den Zustand (Offset) für Killerwünsche."""

    def __init__(self):
        self.repository = WishRepository()
        self.offset_counter = 0

    def get_current_wishes(self):
        """Ruft die Wünsche für den aktuellen Offset ab."""
        return self.repository.get_wishes(self.offset_counter)

    def advance_offset(self):
        """Erhöht den Offset und setzt ihn auf 0 zurück, falls das Ende erreicht ist (Hotkeys)."""
        total_wishes = self.repository.count_total_wishes()

        self.offset_counter += 2

        if self.offset_counter >= total_wishes and total_wishes > 0:
            self.offset_counter = 0
        elif total_wishes == 0:
            self.offset_counter = 0

        wishes_log.info(f'Offset aktualisiert auf: {self.offset_counter}')
        return self.offset_counter

    def add_new_wish(self, wunsch, user_name):
        """Fügt einen Wunsch hinzu und loggt den Vorgang."""
        if not wunsch or not user_name:
            raise ValueError("Wunsch und Benutzername dürfen nicht leer sein.")

        self.repository.add_wish(wunsch, user_name)
        wishes_log.info(f'Neuer Wunsch hinzugefügt von {user_name}: {wunsch}')

    def reset_wishes(self):
        """Löscht alle Wünsche und setzt den Offset zurück."""
        self.repository.delete_all_wishes()
        self.offset_counter = 0
        wishes_log.info("Datenbank erfolgreich zurückgesetzt.")