import json
import time
import random
import threading
from external.settings_manager import SettingsManager
from utils import server_log


class WheelService:
    def __init__(self):
        # ÄNDERUNG: Explizit in den wheel_overlay Ordner
        self.settings_manager = SettingsManager('wheel_overlay/settings.json')
        self.current_state = None  # {winner: ..., rotation: ...}
        self.last_spin_time = 0

        # Initiale Settings laden/erstellen
        s = self.settings_manager.load_settings()
        if "fields" not in s:
            s["fields"] = [0, 2, 5, 0, 1.5, 0, 3, 10]
        if "min_bet" not in s:
            s["min_bet"] = 5
        self.settings_manager.save_settings(s)

    def get_settings(self):
        return self.settings_manager.load_settings()

    def update_settings(self, new_settings):
        self.settings_manager.save_settings(new_settings)

    def get_current_state(self):
        return self.current_state

    def handle_spin(self, user, args):
        from services.service_provider import currency_service_instance, twitch_service_instance

        # 1. Cooldown Check
        settings = self.get_settings()
        cooldown = settings.get("cooldown_seconds", 0)
        if time.time() - self.last_spin_time < cooldown:
            twitch_service_instance.send_message(f"@{user} Warte noch kurz! ⏳")
            return False, "Cooldown"

        # 2. Einsatz parsen
        bet = 0
        try:
            if not args:
                raise ValueError
            if args[0].lower() == "all":
                bet = currency_service_instance.get_balance(user)
            else:
                bet = int(args[0])
        except:
            twitch_service_instance.send_message(f"@{user} Nutzung: !spin <Einsatz>")
            return False, "Usage Error"

        # 3. Limits prüfen
        min_bet = settings.get("min_bet", 5)
        max_bet = settings.get("max_bet", 1000)

        if bet < min_bet:
            twitch_service_instance.send_message(f"@{user} Min. Einsatz ist {min_bet}.")
            return False, "Min Bet"
        if bet > max_bet:
            twitch_service_instance.send_message(f"@{user} Max. Einsatz ist {max_bet}.")
            return False, "Max Bet"

        # 4. Geld abziehen
        if not currency_service_instance.remove_points(user, bet):
            twitch_service_instance.send_message(f"@{user} Zu wenig Punkte!")
            return False, "No Money"

        # 5. Drehen!
        self.last_spin_time = time.time()
        fields = settings.get("fields", [0, 2, 0, 1.5])
        multiplier = random.choice(fields)

        win_amount = int(bet * multiplier)

        # State für Overlay setzen
        self.current_state = {
            "winner": user,
            "bet": bet,
            "multiplier": multiplier,
            "win_amount": win_amount,
            "timestamp": time.time()
        }

        server_log.info(f"🎡 SPIN: {user} setzt {bet} -> x{multiplier} = {win_amount}")

        # Gewinn auszahlen (verzögert, damit Animation passt? Hier sofort logisch, Nachricht später)
        if win_amount > 0:
            currency_service_instance.add_points(user, win_amount)

        # Ergebnis-Nachricht baut der TwitchService (verzögert) oder hier direkt
        # Wir geben es zurück, damit TwitchService es senden kann
        if multiplier > 1:
            return True, f"Glückwunsch! x{multiplier} -> +{win_amount} Coins! 🎉"
        elif multiplier == 1:
            return True, f"Einsatz zurück. Nichts passiert."
        else:
            return True, f"Leider verloren. Viel Glück beim nächsten Mal!"