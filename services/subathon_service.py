from external.settings_manager import SettingsManager
from utils import server_log

class SubathonService:
    """Kapselt das Lesen/Schreiben der Subathon-Konfiguration über den SettingsManager."""
    def __init__(self):
        # Nutzt den SettingsManager, um die subathon_overlay/settings.json zu verwalten
        self.settings_manager = SettingsManager('subathon_overlay/settings.json')
        server_log.info("SubathonService initialisiert.")

    def get_current_settings(self):
        """Ruft die aktuellen Subathon-Einstellungen ab oder gibt einen Standardwert zurück."""
        try:
            return self.settings_manager.load_settings()
        except FileNotFoundError:
            # KORREKTUR: Standardwerte an die neue JSON-Struktur angepasst
            return {
                "animations_time": "3",
                "coins": {
                    "value": "3 Seconds",
                    "active": True
                },
                "subscribe": {
                    "value": "500 Seconds",
                    "active": True
                },
                "follow": {
                    "value": "10 Seconds",
                    "active": True
                },
                "share": {
                    "value": "0.1 Seconds",
                    "active": True
                },
                "like": {
                    "value": "0.1 Seconds",
                    "active": True
                },
                "chat": {
                    "value": "0 Seconds",
                    "active": False
                }
            }

    def update_settings(self, new_settings):
        """Speichert neue Subathon-Einstellungen."""
        # Diese Methode ist generisch und funktioniert ohne Änderung
        self.settings_manager.save_settings(new_settings)
        server_log.info(f"Subathon-Einstellungen aktualisiert: {new_settings}")