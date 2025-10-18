# KORREKTUR: Verwende absolute Importe
from external.settings_manager import SettingsManager
from utils import server_log


class SubathonService:
    """Verwaltet die Geschäftslogik für den Subathon-Timer und die Regeln."""

    def __init__(self):
        self.settings_manager = SettingsManager('subathon_overlay/settings.json')

    def get_current_settings(self):
        """Ruft die aktuellen Subathon-Einstellungen ab oder gibt einen Standardwert zurück."""
        try:
            return self.settings_manager.load_settings()
        except FileNotFoundError:
            server_log.warning("Subathon settings.json nicht gefunden. Verwende Standardwerte.")
            return {
                "timer_end_timestamp": "2025-01-01T00:00:00Z",
                "rules": ["Followers add 5s", "Subs add 60s"],
                "initial_time_seconds": 3600
            }
        except Exception as e:
            server_log.error(f"Fehler beim Laden der Subathon-Einstellungen: {e}")
            raise

    def update_settings(self, new_settings):
        """Speichert neue Subathon-Einstellungen."""
        self.settings_manager.save_settings(new_settings)