import uuid
import json
import os
import threading  # Wichtig für die Sequenz
import time  # Wichtig für die Sequenz
from external.settings_manager import SettingsManager
from utils import server_log
from config import get_path


class CommandService:
    """
    Verwaltet die Befehls-Warteschlange (commands.json),
    die Einstellungen (settings.json) und
    den aktiven Befehl (active.json).
    """

    def __init__(self):
        # Manager für die Haupt-Befehlsliste
        self.settings_manager = SettingsManager('commands_overlay/commands.json')
        # Manager für den *aktuell* sichtbaren Befehl
        self.active_command_manager = SettingsManager('commands_overlay/active.json')
        # Manager für die Einstellungen (Anzeigedauer)
        self.config_manager = SettingsManager('commands_overlay/settings.json')

        self._loop_thread = None  # Hält den Thread, der die Sequenz abspielt
        self._initialize_files()  # Stellt sicher, dass alle 3 JSON-Dateien existieren

    def _initialize_files(self):
        """Stellt sicher, dass alle 3 JSON-Dateien existieren und das korrekte Format haben."""
        # 1. commands.json (Die Liste aller Befehle)
        try:
            commands = self.get_all_commands()
            # Prüfen, ob die Datei leer ist oder das Format veraltet ist (fehlt 'costs')
            if not commands or (commands and 'costs' not in commands[0]):
                server_log.warning("commands.json nicht gefunden oder veraltet. Erstelle/Konvertiere...")

                default_texts = [cmd.get("text", "!example") for cmd in commands if cmd.get("text")]
                if not default_texts:
                    default_texts = [
                        "!boom 100 Whieties",
                        "!mimimi 100 Whieties",
                        "!niclas 100 Whieties"
                    ]

                new_commands = [{"id": str(uuid.uuid4()), "text": txt, "costs": "100"} for txt in default_texts]
                self.settings_manager.save_settings(new_commands)

        except (FileNotFoundError, IndexError, json.JSONDecodeError, TypeError):
            # Datei existiert nicht oder ist kaputt, mit Beispielen neu erstellen
            server_log.info("commands.json nicht gefunden oder kaputt. Erstelle neu...")
            self.settings_manager.save_settings([
                {"id": str(uuid.uuid4()), "text": "!boom 100 Whieties", "costs": "100"},
                {"id": str(uuid.uuid4()), "text": "!mimimi 100 Whieties", "costs": "100"},
                {"id": str(uuid.uuid4()), "text": "!niclas 100 Whieties", "costs": "100"},
            ])

        # 2. active.json (Der aktuell sichtbare Befehl)
        try:
            self.get_active_command()
        except (FileNotFoundError, json.JSONDecodeError):
            self.active_command_manager.save_settings({})  # Als leeres Objekt initialisieren

        # 3. settings.json (Anzeigedauer)
        try:
            self.get_settings()
        except (FileNotFoundError, json.JSONDecodeError):
            self.config_manager.save_settings({"display_duration_seconds": 5})

    # --- Einstellungs-Getter/Setter (Dauer) ---
    def get_settings(self):
        """Lädt die Einstellungen (z.B. Dauer) aus commands_overlay/settings.json"""
        return self.config_manager.load_settings()

    def save_settings(self, settings_data):
        """Speichert die Einstellungen (z.B. Dauer)"""
        self.config_manager.save_settings(settings_data)
        server_log.info(f"Command-Einstellungen gespeichert: {settings_data}")

    # --- CRUD für die Befehlsliste (commands.json) ---
    def get_all_commands(self):
        """Lädt alle Commands aus der Hauptliste (commands.json)."""
        try:
            return self.settings_manager.load_settings()
        except (FileNotFoundError, json.JSONDecodeError):
            return []

    def add_command(self, text, costs):
        """Fügt einen neuen Command zur Hauptliste hinzu."""
        if not text or not costs:
            raise ValueError("Text und Kosten dürfen nicht leer sein.")
        commands = self.get_all_commands()
        new_command = {"id": str(uuid.uuid4()), "text": text, "costs": str(costs)}
        commands.append(new_command)
        self.settings_manager.save_settings(commands)
        server_log.info(f"Command hinzugefügt: {text}")
        return new_command

    def update_command(self, command_id, new_text, new_costs):
        """Aktualisiert einen existierenden Command."""
        if not new_text or not new_costs:
            raise ValueError("Text und Kosten dürfen nicht leer sein.")
        commands = self.get_all_commands()
        command_found = False
        for cmd in commands:
            if cmd.get('id') == command_id:
                cmd['text'] = new_text
                cmd['costs'] = str(new_costs)
                command_found = True
                break
        if not command_found:
            raise ValueError("Command-ID nicht gefunden.")
        self.settings_manager.save_settings(commands)
        server_log.info(f"Command {command_id} aktualisiert.")

    def delete_command(self, command_id):
        """Löscht einen Command aus der Hauptliste."""
        commands = self.get_all_commands()
        original_count = len(commands)
        commands = [cmd for cmd in commands if cmd.get('id') != command_id]
        if len(commands) == original_count:
            raise ValueError("Command-ID nicht gefunden.")
        self.settings_manager.save_settings(commands)
        server_log.info(f"Command {command_id} gelöscht.")

    # --- Trigger-Logik (Die Show) ---

    def _loop_worker(self, commands_list, duration_sec):
        """
        Diese Funktion läuft im Hintergrund-Thread.
        Sie spielt die gesamte Sequenz nacheinander ab.
        """
        server_log.info(f"Starte Command-Sequenz mit {len(commands_list)} Befehlen...")
        try:
            for cmd in commands_list:
                # 1. Befehl in active.json schreiben (Overlay blendet ein)
                self.active_command_manager.save_settings(cmd)

                # 2. Warten (Anzeigedauer)
                time.sleep(duration_sec)

                # 3. Befehl leeren (Overlay blendet aus)
                self.active_command_manager.save_settings({})

                # 4. Kurze Pause für die Ausblend-Animation (muss zur CSS-Animation passen)
                time.sleep(0.5)

            server_log.info("Command-Sequenz beendet.")
        except Exception as e:
            server_log.error(f"Fehler im Command-Loop-Thread: {e}")
        finally:
            # Sicherstellen, dass am Ende alles leer ist
            self.active_command_manager.save_settings({})
            self._loop_thread = None  # Thread als beendet markieren

    def trigger_command_loop(self):
        """(Webhook / Button) Startet die Sequenz in einem neuen Thread."""

        # Verhindern, dass die Sequenz doppelt läuft
        if self._loop_thread and self._loop_thread.is_alive():
            server_log.warning("Trigger ausgelöst, aber eine Sequenz läuft bereits.")
            return

        commands = self.get_all_commands()
        if not commands:
            server_log.warning("Trigger ausgelöst, aber keine Commands in der Liste.")
            return

        try:
            settings = self.get_settings()
            duration = int(settings.get("display_duration_seconds", 5))
        except Exception:
            duration = 5  # Fallback

        # Starte den Worker in einem Daemon-Thread, um Flask nicht zu blockieren
        self._loop_thread = threading.Thread(
            target=self._loop_worker,
            args=(commands, duration),  # Übergibt die *gesamte* Liste und die Dauer
            daemon=True
        )
        self._loop_thread.start()
        server_log.info("Command-Loop-Thread gestartet.")

    # --- Getter für Overlay (active.json) ---
    def get_active_command(self):
        """Lädt den *einen* aktiven Befehl (active.json)."""
        try:
            return self.active_command_manager.load_settings()
        except (FileNotFoundError, json.JSONDecodeError):
            return {}  # Leeres Objekt