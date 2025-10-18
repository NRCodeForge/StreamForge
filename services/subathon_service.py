from external.settings_manager import SettingsManager
from ..utils import server_log

class SubathonService:
    def __init__(self):
        # Nutzt den SettingsManager, um die subathon_overlay/settings.json zu verwalten
        self.settings_manager = SettingsManager('subathon_overlay/settings.json')
        server_log.info("SubathonService initialisiert.")

    def get_current_settings(self):
        """Ruft die aktuellen Subathon-Einstellungen ab oder gibt einen Standardwert zurück."""
        try:
            return self.settings_manager.load_settings()
        except FileNotFoundError:
            # Standardwerte für den ersten Start
            return {
                "timer_end_timestamp": "2025-01-01T00:00:00Z",
                "rules": ["Followers add 5s", "Subs add 60s"],
                "initial_time_seconds": 3600 # 1 Stunde
            }

    def update_settings(self, new_settings):
        """Speichert neue Subathon-Einstellungen."""
        # Hier könnte Logik zur Validierung der Zeitstempel stattfinden
        self.settings_manager.save_settings(new_settings)
        server_log.info(f"Subathon-Einstellungen aktualisiert: {new_settings}")