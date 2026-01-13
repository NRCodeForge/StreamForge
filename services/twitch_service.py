import socket
import threading
import time
from collections import deque

from external.Twitch_API import twitch_log
from utils import server_log
from config import APP_VERSION
from external.settings_manager import SettingsManager


class TwitchService:
    def __init__(self):
        self.sock = None
        self.running = False
        self.username = ""
        self.oauth_token = ""
        self.channel = ""

        self.message_timestamps = deque()
        self.connected = False

        # ÄNDERUNG: Speichert API-Daten jetzt im 'external' Ordner!
        self.settings_manager = SettingsManager("external/twitch_settings.json")
        self.settings = self.settings_manager.load_settings()

    def try_auto_start(self):
        """Versucht beim Start automatisch einzuloggen."""
        user = self.settings.get("twitch_username", "")
        token = self.settings.get("twitch_token", "")

        if user and token:
            server_log.info(f"Twitch Auto-Login gefunden für: {user}")
            self.update_credentials(user, token)
        else:
            server_log.info("Kein Twitch Auto-Login konfiguriert.")

    def get_settings(self):
        self.settings = self.settings_manager.load_settings()
        return self.settings

    def save_settings(self, new_settings):
        self.settings_manager.save_settings(new_settings)
        self.settings = new_settings
        server_log.info("Twitch Einstellungen gespeichert.")

    def update_credentials(self, username, token):
        self.username = username.lower()
        self.oauth_token = token if token.startswith("oauth:") else f"oauth:{token}"
        self.channel = self.username

        self.settings["twitch_username"] = self.username
        self.settings["twitch_token"] = token
        self.save_settings(self.settings)

        if self.running:
            self.stop()
            time.sleep(1)

        if self.username and "oauth:" in self.oauth_token:
            self.start()

    def start(self):
        self.running = True
        threading.Thread(target=self._connection_loop, daemon=True, name="TwitchBot").start()
        threading.Thread(target=self._metrics_loop, daemon=True, name="TwitchMetrics").start()

    def stop(self):
        self.running = False
        if self.sock:
            try:
                self.sock.close()
            except:
                pass
        self.connected = False
        server_log.info("Twitch Service gestoppt.")

    def send_message(self, message):
        if not self.connected or not self.sock: return
        try:
            cmd = f"PRIVMSG #{self.channel} :{message}\r\n"
            self.sock.send(cmd.encode("utf-8"))
            server_log.info(f"🤖 Bot: {message}")
        except:
            pass

    def get_currency_name(self):
        """Holt den aktuellen Währungsnamen sicher aus dem CurrencyService."""
        try:
            from services.service_provider import currency_service_instance
            if hasattr(currency_service_instance, "currency_name"):
                return currency_service_instance.currency_name
            if hasattr(currency_service_instance, "settings"):
                return currency_service_instance.settings.get("currency_name", "Whieties")
        except:
            pass
        return self.settings.get("currency_name", "Whieties")

    def _connection_loop(self):
        host = "irc.chat.twitch.tv"
        port = 6667
        while self.running:
            try:
                self.sock = socket.socket()
                self.sock.connect((host, port))
                self.sock.send(f"PASS {self.oauth_token}\r\n".encode("utf-8"))
                self.sock.send(f"NICK {self.username}\r\n".encode("utf-8"))
                self.sock.send("CAP REQ :twitch.tv/tags twitch.tv/commands twitch.tv/membership\r\n".encode("utf-8"))
                self.sock.send(f"JOIN #{self.channel}\r\n".encode("utf-8"))
                self.connected = True
                server_log.info(f"Twitch Connected als {self.username}")

                buffer = ""
                while self.running:
                    data = self.sock.recv(2048).decode("utf-8")
                    if not data: break
                    buffer += data
                    lines = buffer.split("\r\n")
                    buffer = lines.pop()
                    for line in lines: self._process_line(line)
            except:
                self.connected = False
                time.sleep(5)

    def _process_line(self, line):
        if line.startswith("PING"):
            payload = line.split(" ", 1)[1] if " " in line else ":tmi.twitch.tv"
            try:
                self.sock.send(f"PONG {payload}\r\n".encode("utf-8"))
            except:
                pass
            return

        try:
            tags = {}
            if line.startswith("@"):
                parts = line.split(" ", 1)
                tag_str = parts[0][1:]
                line = parts[1]
                for item in tag_str.split(";"):
                    if "=" in item:
                        k, v = item.split("=", 1)
                        tags[k] = v
            if "PRIVMSG" in line: self._handle_message(line, tags)
            if "USERNOTICE" in line: self._handle_usernotice(tags)
        except Exception as e:
            server_log.error(f"Parse Error: {e}")

    def _handle_message(self, line, tags):
        from services.service_provider import (
            currency_service_instance,
            subathon_service_instance,
            wheel_service_instance,
            wish_service_instance
        )

        c_name = self.get_currency_name()

        self.message_timestamps.append(time.time())
        user = tags.get("display-name", "Unknown")

        # 1. Subathon Timer (Chat Aktivität)
        subathon_service_instance.on_twitch_message(user)

        # 2. Punkte für Nachricht
        pts_msg = int(self.settings.get("currency_per_message", 0))
        if pts_msg > 0:
            currency_service_instance.add_points(user, pts_msg)

        # 3. Bits handling
        if "bits" in tags:
            try:
                bits = int(tags["bits"])
                server_log.info(f"💎 BITS: {user} - {bits} Bits")
                subathon_service_instance.on_twitch_bits(user, bits)
                factor = float(self.settings.get("currency_per_bit", 0))
                if factor > 0:
                    amount = int(bits * factor)
                    currency_service_instance.add_points(user, amount)
                    self.send_message(f"Danke {user} für {bits} Bits! (+{amount} {c_name})")
            except Exception as e:
                server_log.error(f"Bits Error: {e}")

        # 4. Commands Parsing
        parts = line.split("PRIVMSG", 1)
        if len(parts) > 1:
            msg_content = parts[1].split(":", 1)[1].strip()
            args = msg_content.split(" ")
            cmd = args[0].lower()

            if cmd == "!version":
                self.send_message(f"StreamForge Version: {APP_VERSION} 🛠️")

            elif cmd in ["!score", "!points", "!cash"]:
                if self.settings.get("currency_cmd_score_active", True):
                    bal = currency_service_instance.get_balance(user)
                    self.send_message(f"@{user}, du hast {bal} {c_name}.")

            elif cmd == "!send":
                if self.settings.get("currency_cmd_send_active", True):
                    if len(args) < 3:
                        self.send_message(f"@{user}, Nutzung: !send <Name> <Menge>")
                    else:
                        recipient = args[1].replace("@", "")
                        try:
                            amount = int(args[2])
                            success, msg = currency_service_instance.transfer(user, recipient, amount)
                            self.send_message(f"@{user}: {msg}")
                        except ValueError:
                            self.send_message("Bitte eine gültige Zahl eingeben.")

            # --- WHEEL COMMAND (!spin) ---

            elif cmd == "!spin":
                        spin_args = args[1:]
                        server_log.info(f"🎰 !spin von {user}")
                        # ÄNDERUNG: Rückgabewerte auffangen und senden
                        success, msg = wheel_service_instance.handle_spin(user, spin_args)
                        if msg:
                            self.send_message(msg)

            # --- PLACE COMMAND (!place) ---
            elif cmd == "!place":
                server_log.info(f"📍 !place von {user}")
                wish_service_instance.check_user_place(user)

    def _handle_usernotice(self, tags):
        from services.service_provider import currency_service_instance, subathon_service_instance

        c_name = self.get_currency_name()

        msg_id = tags.get("msg-id")
        user = tags.get("display-name", "Unknown")
        pts_sub = int(self.settings.get("currency_per_sub", 0))

        server_log.info(f"🔔 SUB EVENT: {msg_id} von {user}")

        if msg_id in ["sub", "resub"]:
            subathon_service_instance.on_twitch_sub(user, is_gift=False)
            if pts_sub > 0:
                currency_service_instance.add_points(user, pts_sub)
                self.send_message(f"Danke für den Sub {user}! (+{pts_sub} {c_name})")

        elif msg_id == "subgift":
            subathon_service_instance.on_twitch_sub(user, is_gift=True)
            if pts_sub > 0:
                currency_service_instance.add_points(user, pts_sub)

        elif msg_id == "submysterygift":
            count = int(tags.get("msg-param-mass-gift-count", "1"))
            server_log.info(f"💣 GiftBomb von {user}: {count} Subs")
            for _ in range(count):
                subathon_service_instance.on_twitch_sub(user, is_gift=True)

            total = count * pts_sub
            if total > 0:
                currency_service_instance.add_points(user, total)
                self.send_message(f"WOW! {count} Gift-Subs von {user}! (+{total} {c_name})")

    def _metrics_loop(self):
        while True:
            time.sleep(60)
            while self.message_timestamps and self.message_timestamps[0] < time.time() - 60:
                self.message_timestamps.popleft()

    def get_chat_minute(self):
        return len(self.message_timestamps)

    def get_status(self):
        return {"connected": self.connected, "username": self.username}

    def handle_spin_command(self, username, args):
        try:
            from services.service_provider import wheel_service_instance

            # Logik ausführen
            success, msg = wheel_service_instance.handle_spin(username, args)

            # WICHTIG: Die Nachricht IMMER senden, wenn eine vorhanden ist
            if msg:
                self.send_message(msg)

        except Exception as e:
            twitch_log.error(f"Fehler bei !spin: {e}")