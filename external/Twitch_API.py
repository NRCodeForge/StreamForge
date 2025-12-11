import threading
import asyncio
import logging
from twitchio.ext import commands
from config import LOG_FILE_TWITCH

# Logging einrichten
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] [TWITCH] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
    handlers=[logging.FileHandler(LOG_FILE_TWITCH, encoding='utf-8'), logging.StreamHandler()]
)
twitch_log = logging.getLogger("TwitchAPI")


class TwitchBot(commands.Bot):
    def __init__(self, token, channel, parent_api):
        super().__init__(token=token, prefix='!', initial_channels=[channel])
        self.parent_api = parent_api
        self.channel_name = channel

    async def event_ready(self):
        twitch_log.info(f"✅ Eingeloggt als {self.nick} | Kanal: {self.channel_name}")

    async def event_message(self, message):
        if message.echo: return

        username = message.author.name
        content = message.content

        # 1. Normale Nachricht (für Timer & Subathon Logik)
        self.parent_api.notify_message(username)

        # 2. BITS
        if 'bits' in message.tags:
            try:
                bits_amount = int(message.tags['bits'])
                twitch_log.info(f"💎 BITS: {username} hat {bits_amount} Bits gespendet!")
                self.parent_api.notify_bits(username, bits_amount)
            except:
                pass

        # 3. COMMANDS
        if content.startswith('!'):
            parts = content.split(' ')
            cmd = parts[0].lower()
            args = parts[1:] if len(parts) > 1 else []

            if cmd == "!place":
                twitch_log.info(f"❗ Command !place von {username}")
                self.parent_api.handle_place_command(username)

            elif cmd == "!spin":
                twitch_log.info(f"🎰 Command !spin von {username} (Args: {args})")
                self.parent_api.handle_spin_command(username, args)

    async def event_usernotice(self, message):
        """Behandelt Subs, Resubs, GiftBombs."""
        tags = message.tags
        msg_id = tags.get('msg-id', '')
        username = tags.get('display-name') or tags.get('login') or "Unknown"

        if msg_id in ('sub', 'resub'):
            twitch_log.info(f"⭐ Sub/Resub: {username}")
            self.parent_api.notify_sub(username, is_gift=False)

        elif msg_id in ('subgift', 'anonsubgift'):
            # Bei Giftbombs kommt dies pro Geschenk einmal
            recipient = tags.get('msg-param-recipient-display-name', 'Unknown')
            twitch_log.info(f"🎁 Gift-Sub: {username} -> {recipient}")
            self.parent_api.notify_sub(username, is_gift=True)


class Twitch_API_Wrapper:
    def __init__(self, token, channel):
        self.token = token
        self.channel = channel
        self.bot = None
        self.thread = None
        self.running = False

    def start(self):
        if self.running: return
        self.running = True
        self.thread = threading.Thread(target=self._run, daemon=True, name="TwitchBotThread")
        self.thread.start()

    def stop(self):
        self.running = False
        if self.bot and self.bot.loop:
            try:
                asyncio.run_coroutine_threadsafe(self.bot.close(), self.bot.loop)
            except:
                pass

    def _run(self):
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        self.bot = TwitchBot(self.token, self.channel, self)
        try:
            self.bot.run()
        except Exception as e:
            twitch_log.error(f"Twitch Bot abgestürzt: {e}")

    # --- ACTION METHODS ---

    def send_message(self, message):
        """Sendet eine Nachricht in den Chat."""
        if self.bot and self.bot.loop and self.running:
            try:
                # Wir holen den Channel aus dem Cache oder erstellen ihn
                chan = self.bot.get_channel(self.channel)
                if chan:
                    asyncio.run_coroutine_threadsafe(chan.send(message), self.bot.loop)
                else:
                    twitch_log.warning("Konnte Channel nicht finden zum Senden.")
            except Exception as e:
                twitch_log.error(f"Fehler beim Senden der Nachricht: {e}")

    # --- SERVICE CALLS ---

    def handle_place_command(self, username):
        try:
            from services.service_provider import wish_service_instance
            wish_service_instance.check_user_place(username)
        except Exception as e:
            twitch_log.error(f"Fehler bei !place: {e}")

    def handle_spin_command(self, username, args):
        try:
            from services.service_provider import wheel_service_instance

            # Logik ausführen
            success, error_msg = wheel_service_instance.handle_spin(username, args)

            # Falls ein Fehler auftrat (z.B. zu wenig Geld), Nachricht senden
            if not success and error_msg:
                self.send_message(error_msg)

        except Exception as e:
            twitch_log.error(f"Fehler bei !spin: {e}")

    def notify_message(self, username):
        try:
            from services.service_provider import subathon_service_instance
            subathon_service_instance.on_twitch_message(username)
        except:
            pass

    def notify_bits(self, username, amount):
        try:
            from services.service_provider import subathon_service_instance
            subathon_service_instance.on_twitch_bits(username, amount)
        except:
            pass

    def notify_sub(self, username, is_gift):
        try:
            from services.service_provider import subathon_service_instance
            subathon_service_instance.on_twitch_sub(username, is_gift)
        except:
            pass