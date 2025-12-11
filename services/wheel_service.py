import time
import random
import threading
import requests
import logging
from external.settings_manager import SettingsManager

logger = logging.getLogger("WheelService")


class WheelService:
    def __init__(self):
        # Settings Manager für das Rad
        self.settings_manager = SettingsManager("wheel_settings.json")
        self._ensure_defaults()

        # Status für das Overlay
        self.active_spin = None  # Speichert Daten des aktuellen Spins
        self.lock = threading.Lock()  # Verhindert gleichzeitiges Drehen

    def _ensure_defaults(self):
        """Lädt Settings oder erstellt Standardwerte."""
        settings = self.settings_manager.load_settings()
        if not settings:
            default_segments = [
                {"text": "2x", "value": 2.0, "color": "#2ecc71", "weight": 10},
                {"text": "1.5x", "value": 1.5, "color": "#f1c40f", "weight": 20},
                {"text": "1.2x", "value": 1.2, "color": "#3498db", "weight": 30},
                {"text": "1x", "value": 1.0, "color": "#95a5a6", "weight": 30},
                {"text": "0.5x", "value": 0.5, "color": "#e67e22", "weight": 20},
                {"text": "0x", "value": 0.0, "color": "#e74c3c", "weight": 40},
                {"text": "JACKPOT", "value": 10.0, "color": "#9b59b6", "weight": 1}
            ]
            settings = {
                "min_bet": 5,
                "max_bet": 1000,
                "segments": default_segments
            }
            self.settings_manager.save_settings(settings)
        return settings

    def get_settings(self):
        return self.settings_manager.load_settings()

    def update_settings(self, new_settings):
        self.settings_manager.save_settings(new_settings)

    def _get_pfp(self, username):
        """Holt das Profilbild via Twitch Helix API."""
        # --- LAZY IMPORT (verhindert Circular Import) ---
        from services.service_provider import twitch_service_instance
        # ------------------------------------------------

        try:
            # HINWEIS: Stelle sicher, dass TwitchService eine get_settings() Methode hat,
            # oder greife direkt auf twitch_service_instance.settings zu.
            # Hier nehme ich an, du hast get_settings() implementiert.
            if hasattr(twitch_service_instance, 'get_settings'):
                ts = twitch_service_instance.get_settings()
            else:
                ts = twitch_service_instance.settings  # Fallback auf Attribut

            token = ts.get("oauth_token")
            # Prüfen ob der Key in deinen Settings 'client_id' oder 'twitch_client_id' heißt
            client_id = ts.get("client_id", ts.get("twitch_client_id", ""))

            if not token:
                return ""

            headers = {
                "Authorization": f"Bearer {token}",
                "Client-Id": client_id if client_id else "gp762nuuoqcoxypju8c569th9wz7q5"
            }

            url = f"https://api.twitch.tv/helix/users?login={username}"
            r = requests.get(url, headers=headers)
            if r.status_code == 200:
                data = r.json()
                if data.get("data"):
                    return data["data"][0]["profile_image_url"]
        except Exception as e:
            logger.error(f"Fehler beim PFP laden: {e}")
        return ""

    def handle_spin(self, user_name, args):
        """Hauptlogik für !spin"""
        # --- LAZY IMPORT ---
        from services.service_provider import currency_service_instance
        # -------------------

        if self.active_spin:
            return False, "Das Rad dreht sich bereits!"

        settings = self.get_settings()
        min_bet = int(settings.get("min_bet", 5))
        max_bet = int(settings.get("max_bet", 1000))

        # 1. Einsatz parsen
        try:
            if not args:
                amount = min_bet
            else:
                amount = int(args[0])
        except ValueError:
            amount = min_bet

        if amount < min_bet: amount = min_bet
        if amount > max_bet: amount = max_bet

        # 2. Guthaben prüfen
        balance = currency_service_instance.get_balance(user_name)
        if balance < amount:
            return False, f"@{user_name} Du hast nicht genug Punkte! (Benötigt: {amount}, Aktuell: {balance})"

        with self.lock:
            # 3. Einsatz abziehen
            currency_service_instance.add_points(user_name, -amount)

            # 4. Ergebnis berechnen
            segments = settings.get("segments", [])
            if not segments:
                return False, "Fehler: Keine Segmente konfiguriert."

            weights = [s.get("weight", 10) for s in segments]
            result_segment = random.choices(segments, weights=weights, k=1)[0]
            result_index = segments.index(result_segment)

            multiplier = float(result_segment.get("value", 0))
            win_amount = int(amount * multiplier)

            # 5. PFP holen
            pfp_url = self._get_pfp(user_name)

            # 6. Status setzen
            self.active_spin = {
                "user": user_name,
                "pfp": pfp_url,
                "bet": amount,
                "win_amount": win_amount,
                "segments": segments,
                "target_index": result_index,
                "timestamp": time.time()
            }

            # 7. Thread starten
            threading.Thread(target=self._finish_spin_later, args=(user_name, win_amount), daemon=True).start()

            return True, None

    def _finish_spin_later(self, user_name, win_amount):
        """Wartet auf Animation und schreibt Gewinn gut."""
        # --- LAZY IMPORT ---
        from services.service_provider import currency_service_instance, twitch_service_instance
        # -------------------

        time.sleep(8)

        if win_amount > 0:
            currency_service_instance.add_points(user_name, win_amount)
            msg = f"@{user_name} Glückwunsch! {win_amount} deinem Konto hinzugefügt."
        else:
            msg = f"@{user_name} Leider nichts gewonnen. Viel Glück beim nächsten Mal!"

        twitch_service_instance.send_message(msg)

        time.sleep(2)
        self.active_spin = None

    def get_current_state(self):
        return self.active_spin