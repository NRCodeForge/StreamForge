import socket
import threading
import time
import re
from collections import deque
from utils import server_log
from config import APP_VERSION


class TwitchService:
    def __init__(self):
        self.sock = None
        self.running = False
        self.username = ""
        self.oauth_token = ""
        self.channel = ""

        self.message_timestamps = deque()
        self.connected = False

        # Lazy Import für Settings beim Start
        from services.service_provider import like_service_instance
        self.settings = like_service_instance.settings_manager.load_settings()
        self.currency_name = self.settings.get("currency_name", "Coins")

    def update_credentials(self, username, token):
        self.username = username.lower()
        self.oauth_token = token if token.startswith("oauth:") else f"oauth:{token}"
        self.channel = self.username

        # Settings neu laden (Lazy Import)
        from services.service_provider import like_service_instance
        self.settings = like_service_instance.settings_manager.load_settings()
        self.currency_name = self.settings.get("currency_name", "Coins")

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
        # Lazy Import hier, damit der Service Provider schon fertig geladen ist
        from services.service_provider import currency_service_instance

        self.message_timestamps.append(time.time())
        user = tags.get("display-name", "Unknown")

        # --- 1. PUNKTE FÜR NACHRICHT ---
        pts_msg = int(self.settings.get("currency_per_message", 0))
        if pts_msg > 0:
            currency_service_instance.add_points(user, pts_msg)

        # --- 2. BITS ---
        if "bits" in tags:
            bits = int(tags["bits"])
            factor = float(self.settings.get("currency_per_bit", 0))
            if factor > 0:
                amount = int(bits * factor)
                currency_service_instance.add_points(user, amount)
                self.send_message(f"Danke {user} für {bits} Bits! (+{amount} {self.currency_name})")

        # --- COMMANDS ---
        parts = line.split("PRIVMSG", 1)
        if len(parts) > 1:
            msg_content = parts[1].split(":", 1)[1].strip()
            args = msg_content.split(" ")
            cmd = args[0].lower()

            if cmd == "!version":
                self.send_message(f"StreamForge Version: {APP_VERSION} 🛠️")

            # !score / !points
            elif cmd in ["!score", "!points", "!cash"]:
                if self.settings.get("currency_cmd_score_active", True):
                    bal = currency_service_instance.get_balance(user)
                    self.send_message(f"@{user}, du hast {bal} {self.currency_name}.")

            # !send <user> <amount>
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

    def _handle_usernotice(self, tags):
        from services.service_provider import currency_service_instance

        msg_id = tags.get("msg-id")
        user = tags.get("display-name", "Unknown")

        # --- PUNKTE FÜR SUBS ---
        pts_sub = int(self.settings.get("currency_per_sub", 0))

        if msg_id in ["sub", "resub"]:
            if pts_sub > 0:
                currency_service_instance.add_points(user, pts_sub)
                self.send_message(f"Danke für den Sub {user}! (+{pts_sub} {self.currency_name})")

        elif msg_id == "subgift":
            # Gifter bekommt Punkte
            if pts_sub > 0:
                currency_service_instance.add_points(user, pts_sub)

        elif msg_id == "submysterygift":
            # Giftbomb
            count = int(tags.get("msg-param-mass-gift-count", "1"))
            total = count * pts_sub
            if total > 0:
                currency_service_instance.add_points(user, total)
                self.send_message(f"WOW! {count} Gift-Subs von {user}! (+{total} {self.currency_name})")

    def _metrics_loop(self):
        while True:
            time.sleep(60)
            while self.message_timestamps and self.message_timestamps[0] < time.time() - 60:
                self.message_timestamps.popleft()

    def get_chat_minute(self):
        return len(self.message_timestamps)

    def get_status(self):
        return {"connected": self.connected, "username": self.username}