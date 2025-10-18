import json
import os
import sys

# KORREKTUR: Verwende absolute Imports
from config import get_path
from utils import server_log

class SettingsManager:
    """Verwaltet das Lesen und Schreiben von JSON-Einstellungsdateien."""
    def __init__(self, relative_path):
        self.absolute_path = get_path(relative_path)
        server_log.info(f"SettingsManager für {relative_path} initialisiert: {self.absolute_path}")

    def load_settings(self):
        """Lädt die Einstellungen aus der JSON-Datei."""
        try:
            with open(self.absolute_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            server_log.warning(f"Einstellungsdatei nicht gefunden: {self.absolute_path}")
            raise
        except json.JSONDecodeError as e:
            server_log.error(f"Fehler beim Parsen der JSON-Datei {self.absolute_path}: {e}")
            raise

    def save_settings(self, settings_data):
        """Speichert die Einstellungen in die JSON-Datei."""
        try:
            os.makedirs(os.path.dirname(self.absolute_path), exist_ok=True)
            with open(self.absolute_path, 'w', encoding='utf-8') as f:
                json.dump(settings_data, f, indent=4, ensure_ascii=False)
            server_log.info(f"Einstellungen erfolgreich in {self.absolute_path} gespeichert.")
        except Exception as e:
            server_log.error(f"Fehler beim Speichern der Einstellungen in {self.absolute_path}: {e}")
            raise