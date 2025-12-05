import uuid
import json
import os
import threading
import time
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
        self.settings_manager = SettingsManager('commands_overlay/commands.json')
        self.active_command_manager = SettingsManager('commands_overlay/active.json')
        self.config_manager = SettingsManager('commands_overlay/settings.json')

        self._loop_thread = None
        self._initialize_files()

    def _initialize_files(self):
        """Stellt sicher, dass alle 3 JSON-Dateien existieren und gefüllt sind."""

        # 1. commands.json prüfen
        commands = self.get_all_commands()

        # WICHTIG: Wenn Liste leer ist oder Fehler hat -> Standardwerte schreiben!
        if not commands or len(commands) == 0:
            server_log.info("commands.json war leer. Erstelle Standard-Befehle...")
            default_commands = [
                {"id": str(uuid.uuid4()), "text": "!boom", "costs": "100", "is_superfan": False},
                {"id": str(uuid.uuid4()), "text": "!mimimi", "costs": "100", "is_superfan": False},
                {"id": str(uuid.uuid4()), "text": "!chaos", "costs": "5000", "is_superfan": True},
            ]
            self.settings_manager.save_settings(default_commands)

        # 2. active.json (Leeren beim Start)
        self.active_command_manager.save_settings({})

        # 3. settings.json (Dauer)
        try:
            if not self.config_manager.load_settings():
                raise ValueError("Leer")
        except:
            self.config_manager.save_settings({"display_duration_seconds": 5})

    def get_settings(self):
        return self.config_manager.load_settings()

    def save_settings(self, settings_data):
        self.config_manager.save_settings(settings_data)
        server_log.info(f"Command-Einstellungen gespeichert: {settings_data}")

    # --- CRUD ---
    def get_all_commands(self):
        """Lädt die Liste. Gibt [] zurück bei Fehler."""
        try:
            data = self.settings_manager.load_settings()
            if isinstance(data, list):
                return data
            return []
        except:
            return []

    def add_command(self, text, costs, is_superfan=False):
        if not text or not costs:
            raise ValueError("Text und Kosten dürfen nicht leer sein.")

        commands = self.get_all_commands()
        new_command = {
            "id": str(uuid.uuid4()),
            "text": text,
            "costs": str(costs),
            "is_superfan": is_superfan
        }
        commands.append(new_command)
        self.settings_manager.save_settings(commands)
        server_log.info(f"Command hinzugefügt: {text} (Superfan: {is_superfan})")
        return new_command

    def update_command(self, command_id, new_text, new_costs, is_superfan):
        if not new_text or not new_costs:
            raise ValueError("Text und Kosten dürfen nicht leer sein.")

        commands = self.get_all_commands()
        command_found = False
        for cmd in commands:
            if cmd.get('id') == command_id:
                cmd['text'] = new_text
                cmd['costs'] = str(new_costs)
                cmd['is_superfan'] = is_superfan
                command_found = True
                break

        if not command_found:
            raise ValueError("Command-ID nicht gefunden.")

        self.settings_manager.save_settings(commands)
        server_log.info(f"Command {command_id} aktualisiert.")

    def delete_command(self, command_id):
        commands = self.get_all_commands()
        commands = [cmd for cmd in commands if cmd.get('id') != command_id]
        self.settings_manager.save_settings(commands)
        server_log.info(f"Command {command_id} gelöscht.")

    # --- Trigger-Logik ---
    def _loop_worker(self, commands_list, duration_sec):
        server_log.info(f"Starte Command-Sequenz...")
        try:
            for cmd in commands_list:
                self.active_command_manager.save_settings(cmd)
                time.sleep(duration_sec)
                self.active_command_manager.save_settings({})
                time.sleep(0.5)
            server_log.info("Command-Sequenz beendet.")
        except Exception as e:
            server_log.error(f"Fehler im Loop: {e}")
        finally:
            self.active_command_manager.save_settings({})
            self._loop_thread = None

    def trigger_command_loop(self):
        if self._loop_thread and self._loop_thread.is_alive():
            server_log.warning("Sequenz läuft bereits.")
            return

        commands = self.get_all_commands()
        if not commands:
            server_log.warning("Keine Commands gefunden! Trigger abgebrochen.")
            return

        try:
            settings = self.get_settings()
            duration = int(settings.get("display_duration_seconds", 5))
        except:
            duration = 5

        self._loop_thread = threading.Thread(target=self._loop_worker, args=(commands, duration), daemon=True)
        self._loop_thread.start()
        server_log.info("Command-Loop gestartet.")

    def get_active_command(self):
        try:
            return self.active_command_manager.load_settings()
        except:
            return {}