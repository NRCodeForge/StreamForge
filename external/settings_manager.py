import json
import os
import sys
import logging

# Logger konfigurieren
logger = logging.getLogger("SettingsManager")


class SettingsManager:
    def __init__(self, file_path, default_settings=None):
        """
        Initialisiert den SettingsManager.
        :param file_path: Relativer Pfad zur JSON-Datei (z.B. 'twitch_settings.json' oder 'like_overlay/settings.json').
        :param default_settings: (Optional) Standardwerte.
        """
        self.default_settings = default_settings if default_settings else {}
        # Pfad sofort beim Start korrekt auflösen (Exe vs. Dev Umgebung)
        self.file_path = self._resolve_path(file_path)

    def _resolve_path(self, path):
        """
        Entscheidet, wo die Datei liegt:
        1. Ist es eine EXE? -> Prüfe _internal Ordner für gebündelte Dateien.
        2. Sonst -> Nutze normalen Pfad.
        3. Falls Datei nicht existiert -> Nutze Pfad neben der EXE (für Neuerstellung).
        """
        # Prüfen, ob wir als EXE laufen (Frozen)
        if getattr(sys, 'frozen', False):
            # Basispfad ist der Ordner, in dem die .exe liegt
            exe_dir = os.path.dirname(sys.executable)

            # 1. Priorität: Liegt die Datei direkt neben der EXE? (User-Override)
            root_path = os.path.join(exe_dir, path)
            if os.path.exists(root_path):
                return root_path

            # 2. Priorität: Liegt die Datei im _internal Ordner? (Gebündelte Assets)
            # sys._MEIPASS zeigt auf den temporären/_internal Ordner von PyInstaller
            if hasattr(sys, '_MEIPASS'):
                internal_path = os.path.join(sys._MEIPASS, path)
                if os.path.exists(internal_path):
                    return internal_path

            # 3. Fallback: Datei existiert noch nicht (z.B. twitch_settings.json).
            # Wir wollen sie neben der EXE erstellen, damit der User sie findet.
            return root_path

        else:
            # Entwickler-Modus (keine EXE)
            return os.path.abspath(path)

    def load_settings(self):
        """Lädt die Einstellungen. Erstellt Datei neu bei Fehler/Fehlen."""
        # 1. Existenz prüfen (Pfad ist bereits aufgelöst)
        if not os.path.exists(self.file_path):
            logger.warning(f"Datei nicht gefunden: {self.file_path}. Erstelle neu...")
            self.save_settings(self.default_settings)
            return self.default_settings

        # 2. Laden
        try:
            with open(self.file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                if not data and self.default_settings:
                    return self.default_settings
                return data
        except (FileNotFoundError, json.JSONDecodeError) as e:
            logger.error(f"Fehler beim Laden von {self.file_path} ({e}). Reset.")
            self.save_settings(self.default_settings)
            return self.default_settings

    def save_settings(self, settings):
        """Speichert die Einstellungen."""
        try:
            # Ordnerstruktur sicherstellen (wichtig für Unterordner wie 'like_overlay')
            directory = os.path.dirname(self.file_path)
            if directory and not os.path.exists(directory):
                os.makedirs(directory, exist_ok=True)

            with open(self.file_path, 'w', encoding='utf-8') as f:
                json.dump(settings, f, indent=4)
        except Exception as e:
            logger.error(f"Konnte Einstellungen nicht speichern in {self.file_path}: {e}")