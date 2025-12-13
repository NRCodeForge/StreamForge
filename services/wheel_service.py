import time
import random
import json
from external.settings_manager import SettingsManager
from utils import server_log


class WheelService:
    def __init__(self):
        # Settings Manager laden
        self.settings_manager = SettingsManager('wheel_overlay/settings.json')
        # Lade Settings sicher
        self.settings = self.settings_manager.load_settings()

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
        Bereitet die Daten so auf, dass das JS sie direkt verarbeiten kann.
        """
        # 1. Felder aus Settings laden und für JS aufbereiten (Farben & Text)
        raw_fields = self.settings.get("fields", [0, 2])
        segments = []
        # Eine Farbpalette, die sich wiederholt
        colors = ["#3498db", "#e74c3c", "#f1c40f", "#2ecc71", "#9b59b6", "#1abc9c", "#e67e22", "#34495e"]

        for i, val in enumerate(raw_fields):
            segments.append({
                "text": str(val),  # Text für das Segment
                "value": val,  # Wert für Berechnung
                "color": colors[i % len(colors)]  # Farbe zuweisen
            })

        # 2. Basis-Antwort erstellen
        response = {
            "is_spinning": False,
            "segments": segments  # JS erwartet 'segments' mit .color und .text
        }

        # 3. Wenn ein Spin aktiv war, Daten auf oberste Ebene mischen (für JS data.timestamp check)
        if self.last_spin_data:
            response.update(self.last_spin_data)
            # JS erwartet win_amount, wir haben es als 'win' gespeichert -> Mapping
            response["win_amount"] = self.last_spin_data.get("win", 0)

        return response

    def handle_spin(self, user, args):
        """
        Führt den Spin aus.
        Rückgabe: (Success: bool, Message: str)
        """
        try:
            from services.service_provider import currency_service_instance

            # --- 1. COOLDOWN PRÜFEN ---
            cooldown_time = int(self.settings.get("cooldown_seconds", 0))
            if cooldown_time > 0:
                last_time = self.last_spins.get(user, 0)
                elapsed = time.time() - last_time

                if elapsed < cooldown_time:
                    remaining = int(cooldown_time - elapsed)
                    m, s = divmod(remaining, 60)
                    time_str = f"{m} Min {s} Sek" if m > 0 else f"{s} Sek"
                    return False, f"⏳ Warte noch {time_str} für den nächsten Spin."

            # --- 2. EINSATZ LOGIK (AUTO-KORREKTUR) ---
            min_bet = int(self.settings.get("min_bet", 10))
            max_bet = int(self.settings.get("max_bet", 10000))

            # Wenn keine Argumente -> Mindesteinsatz nehmen
            if not args:
                bet_amount = min_bet
            else:
                try:
                    arg = args[0].lower()
                    if arg in ["all", "max"]:
                        # Bei 'all' nehmen wir alles was er hat, aber cappen bei max_bet
                        user_balance = currency_service_instance.get_balance(user)
                        bet_amount = user_balance
                    else:
                        bet_amount = int(args[0])
                except ValueError:
                    return False, "Ungültiger Einsatz."

            # Automatisch auf Min/Max korrigieren (Clamping)
            if bet_amount < min_bet:
                bet_amount = min_bet
            if bet_amount > max_bet:
                bet_amount = max_bet

            # --- 3. GUTHABEN PRÜFEN ---
            current_balance = currency_service_instance.get_balance(user)
            if current_balance < bet_amount:
                return False, f"Nicht genug Punkte (Hast: {current_balance})."

            # --- 4. SPIN DURCHFÜHREN ---
            currency_service_instance.add_points(user, -bet_amount)

            raw_fields = self.settings.get("fields", [0, 0, 0, 2, 2, 5, 10])
            if not raw_fields: raw_fields = [0, 2]

            # WICHTIG: Einen zufälligen INDEX wählen, nicht nur einen Wert!
            # Das JS muss wissen, an welcher Stelle (0 bis N) das Rad stoppen soll.
            target_index = random.randint(0, len(raw_fields) - 1)
            multiplier = raw_fields[target_index]

            win_amount = int(bet_amount * multiplier)

            # Gewinn gutschreiben
            if win_amount > 0:
                currency_service_instance.add_points(user, win_amount)

            # --- 5. DATEN SPEICHERN ---
            self.last_spins[user] = time.time()

            # Daten für Overlay setzen (inklusive target_index für Animation)
            self.last_spin_data = {
                "username": user,
                "bet": bet_amount,
                "multiplier": multiplier,
                "win": win_amount,
                "target_index": target_index,  # WICHTIG: Damit JS weiß, wohin es drehen muss
                "timestamp": time.time()  # WICHTIG: Damit JS den neuen Spin erkennt
            }

            server_log.info(f"🎰 SPIN: {user} setzt {bet_amount} -> x{multiplier} (Index {target_index}) = {win_amount}")

            # Nachricht generieren
            if multiplier > 1:
                return True, f"gewinnt {win_amount}! 🎉"
            elif multiplier == 1:
                return True, f"behält den Einsatz . 😐"
            else:
                return True, f"verliert {bet_amount}. 💸"

        except Exception as e:
            server_log.error(f"Spin Error: {e}")
            return False, "Fehler beim Glücksrad."