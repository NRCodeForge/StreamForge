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
        """Löscht den ältesten Wunsch, erhöht den Offset und setzt ihn ggf. zurück."""

        # NEU: Zuerst den ältesten Wunsch löschen
        self.repository.delete_oldest_wish()

        # Berechne die neue Gesamtzahl *nach* dem Löschen
        total_wishes_after_delete = self.repository.count_total_wishes()

        # Die Logik zur Offset-Erhöhung bleibt ähnlich,
        # aber wir müssen den Offset nicht mehr explizit erhöhen,
        # da durch das Löschen des ersten Elements die nächsten "aufrutschen".
        # Wir müssen nur sicherstellen, dass der Offset zurückgesetzt wird,
        # wenn er das (neue) Ende erreicht.

        # Wenn der aktuelle Offset größer oder gleich der neuen Anzahl ist
        # ODER wenn es keine Wünsche mehr gibt, setze auf 0 zurück.
        if self.offset_counter >= total_wishes_after_delete:
            self.offset_counter = 0
        # Optional: Wenn nach dem Löschen keine Wünsche mehr da sind, auch auf 0 setzen.
        elif total_wishes_after_delete == 0:
            self.offset_counter = 0
        # Wichtig: Wenn der Offset gültig bleibt (also nicht >= total_wishes_after_delete),
        # dann muss er NICHT verändert werden, da der nächste Wunsch automatisch an diese Position rückt.

        wishes_log.info(f'Offset nach Löschen und Prüfung: {self.offset_counter}')
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