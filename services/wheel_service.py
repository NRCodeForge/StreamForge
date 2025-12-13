import time
import random
import json
from external.settings_manager import SettingsManager
from utils import server_log


class WheelService:
    def __init__(self):
        # Settings Manager laden
        self.settings_manager = SettingsManager('wheel_overlay/settings.json')
        self.settings = self.settings_manager.get_settings() if hasattr(self.settings_manager,
                                                                        'get_settings') else self.settings_manager.load_settings()

        # Speicher für Cooldowns: { "username": timestamp }
        self.last_spins = {}

        # Speicher für das Overlay (letzter Dreh)
        self.last_spin_data = None

    def get_settings(self):
        self.settings = self.settings_manager.load_settings()
        return self.settings

    def update_settings(self, new_settings):
        self.settings = new_settings
        self.settings_manager.save_settings(new_settings)

    def get_current_state(self):
        """
        Wird von der Web-API aufgerufen, um dem Overlay Daten zu geben.
        """
        return {
            "is_spinning": False,  # Einfache Status-Flag
            "last_spin": self.last_spin_data,
            "fields": self.settings.get("fields", [0, 2])
        }

    def handle_spin(self, user, args):
        """
        Führt den Spin aus.
        Rückgabe: (Success: bool, Message: str)
        """
        try:
            from services.service_provider import currency_service_instance

            # 1. COOLDOWN PRÜFEN
            cooldown_time = int(self.settings.get("cooldown_seconds", 0))
            if cooldown_time > 0:
                last_time = self.last_spins.get(user, 0)
                elapsed = time.time() - last_time

                if elapsed < cooldown_time:
                    remaining = int(cooldown_time - elapsed)
                    m, s = divmod(remaining, 60)
                    if m > 0:
                        time_str = f"{m} Min {s} Sek"
                    else:
                        time_str = f"{s} Sek"
                    return False, f"⏳ Warte noch {time_str} für den nächsten Spin."

            # 2. Argumente prüfen (Einsatz)
            if not args:
                return False, "Bitte Einsatz angeben: !spin <Menge>"

            try:
                if args[0].lower() in ["all", "max"]:
                    bet_amount = currency_service_instance.get_balance(user)
                else:
                    bet_amount = int(args[0])
            except ValueError:
                return False, "Ungültiger Einsatz."

            # 3. Limits prüfen
            min_bet = int(self.settings.get("min_bet", 10))
            max_bet = int(self.settings.get("max_bet", 10000))

            if bet_amount < min_bet:
                return False, f"Mindesteinsatz ist {min_bet}."
            if bet_amount > max_bet:
                return False, f"Maximaleinsatz ist {max_bet}."

            # 4. Guthaben prüfen
            current_balance = currency_service_instance.get_balance(user)
            if current_balance < bet_amount:
                return False, f"Nicht genug Punkte (Hast: {current_balance})."

            # 5. Spin durchführen
            currency_service_instance.add_points(user, -bet_amount)

            fields = self.settings.get("fields", [0, 0, 0, 2, 2, 5, 10])
            if not fields: fields = [0, 2]

            multiplier = random.choice(fields)
            win_amount = int(bet_amount * multiplier)

            # Gewinn gutschreiben
            if win_amount > 0:
                currency_service_instance.add_points(user, win_amount)

            # 6. Cooldown & Daten setzen
            self.last_spins[user] = time.time()

            # Daten für Overlay speichern
            self.last_spin_data = {
                "username": user,
                "bet": bet_amount,
                "multiplier": multiplier,
                "win": win_amount,
                "timestamp": time.time()
            }

            server_log.info(f"🎰 SPIN: {user} setzt {bet_amount} -> x{multiplier} = {win_amount}")

            # Nachricht generieren
            if multiplier > 1:
                return True, f"gewinnt {win_amount} (x{multiplier})! 🎉"
            elif multiplier == 1:
                return True, f"behält den Einsatz (x1). 😐"
            else:
                return True, f"verliert {bet_amount}. 💸"

        except Exception as e:
            server_log.error(f"Spin Error: {e}")
            return False, "Fehler beim Glücksrad."