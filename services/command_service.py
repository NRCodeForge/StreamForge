import uuid
import threading
import time
from external.settings_manager import SettingsManager
from utils import server_log


class CommandService:
    def __init__(self):
        # Zwei separate Manager: Einen für Settings, einen für die Commands-Liste
        self.settings_manager = SettingsManager('commands_overlay/settings.json')
        self.commands_manager = SettingsManager('commands_overlay/commands.json', default_settings={"list": []})

        self.active_command = None
        self._loop_active = False

    def get_settings(self):
        return self.settings_manager.load_settings()

    def save_settings(self, s):
        self.settings_manager.save_settings(s)

    def get_all_commands(self):
        data = self.commands_manager.load_settings()
        return data.get("list", [])

    def add_command(self, text, costs, is_superfan):
        data = self.commands_manager.load_settings()
        new_cmd = {
            "id": str(uuid.uuid4()),
            "text": text,
            "costs": costs,
            "is_superfan": is_superfan
        }
        if "list" not in data: data["list"] = []
        data["list"].append(new_cmd)
        self.commands_manager.save_settings(data)

    def update_command(self, cmd_id, text, costs, is_superfan):
        data = self.commands_manager.load_settings()
        for c in data.get("list", []):
            if c["id"] == cmd_id:
                c["text"] = text
                c["costs"] = costs
                c["is_superfan"] = is_superfan
                break
        self.commands_manager.save_settings(data)

    def delete_command(self, cmd_id):
        data = self.commands_manager.load_settings()
        data["list"] = [c for c in data.get("list", []) if c["id"] != cmd_id]
        self.commands_manager.save_settings(data)

    def get_active_command(self):
        return self.active_command

    def trigger_command_loop(self):
        if self._loop_active: return
        threading.Thread(target=self._run_loop, daemon=True).start()

    def _run_loop(self):
        self._loop_active = True
        cmds = self.get_all_commands()
        settings = self.get_settings()
        duration = int(settings.get("display_duration_seconds", 5))

        server_log.info(f"▶ Starte Command Loop ({len(cmds)} Commands, je {duration}s)")

        for cmd in cmds:
            self.active_command = cmd
            time.sleep(duration)

        self.active_command = None
        self._loop_active = False
        server_log.info("⏹ Command Loop beendet.")