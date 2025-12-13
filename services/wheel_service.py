import time
import random
import threading
import requests
import logging
from external.settings_manager import SettingsManager

logger = logging.getLogger("WheelService")


class WheelService:
    def __init__(self):
        # Zeigt direkt auf die Datei im Overlay-Ordner
        self.settings_manager = SettingsManager("wheel_overlay/settings.json")
        self._ensure_defaults()

        self.active_spin = None
        self.lock = threading.Lock()

    def _ensure_defaults(self):
        """Erstellt Defaults, falls Datei leer."""
        try:
            settings = self.settings_manager.load_settings()
        except Exception:
            settings = {}

        # Wenn weder segments noch fields da sind, Standard schreiben
        if not settings or ("segments" not in settings and "fields" not in settings):
            default_segments = [
                {"text": "2x", "value": 2.0, "color": "#2ecc71", "weight": 10},
                {"text": "0x", "value": 0.0, "color": "#e74c3c", "weight": 10}
            ]
            self.settings_manager.save_settings({"min_bet": 10, "max_bet": 1000, "segments": default_segments})

    def get_settings(self):
        settings = self.settings_manager.load_settings()
        if not settings:
            return {}

        # --- MAGIE: "fields" (Liste) in "segments" (Objekte) umwandeln ---
        if "fields" in settings and "segments" not in settings:
            raw_fields = settings["fields"]
            segments = []
            # Farbpalette für automatische Färbung
            colors = ["#3498db", "#e74c3c", "#f1c40f", "#2ecc71", "#9b59b6", "#e67e22", "#1abc9c", "#34495e"]

            for i, val in enumerate(raw_fields):
                segments.append({
                    "text": f"{val}x",  # Standardtext (wird im Frontend überschrieben)
                    "value": float(val),  # Der Multiplikator
                    "color": colors[i % len(colors)],  # Rotierende Farben
                    "weight": 1  # Jedes Feld ist gleich groß
                })
            settings["segments"] = segments
        # -----------------------------------------------------------------

        return settings

    def update_settings(self, new_settings):
        self.settings_manager.save_settings(new_settings)

    def _get_pfp(self, username):
        from services.service_provider import twitch_service_instance
        try:
            if hasattr(twitch_service_instance, 'get_settings'):
                ts = twitch_service_instance.get_settings()
            else:
                ts = twitch_service_instance.settings

            token = ts.get("oauth_token")
            client_id = ts.get("client_id", ts.get("twitch_client_id", ""))

            if token:
                headers = {"Authorization": f"Bearer {token}",
                           "Client-Id": client_id if client_id else "gp762nuuoqcoxypju8c569th9wz7q5"}
                r = requests.get(f"https://api.twitch.tv/helix/users?login={username}", headers=headers)
                if r.status_code == 200 and r.json().get("data"):
                    return r.json()["data"][0]["profile_image_url"]
        except Exception as e:
            logger.error(f"PFP Fehler: {e}")
        return ""

    def handle_spin(self, user_name, args):
        from services.service_provider import currency_service_instance

        if self.active_spin:
            return False, "Das Rad dreht sich bereits!"

        settings = self.get_settings()
        if not settings or "segments" not in settings:
            return False, "Fehler: Rad-Konfiguration (fields/segments) fehlt."

        min_bet = int(settings.get("min_bet", 5))
        max_bet = int(settings.get("max_bet", 1000))

        try:
            amount = int(args[0]) if args else min_bet
        except ValueError:
            amount = min_bet

        if amount < min_bet: amount = min_bet
        if amount > max_bet: amount = max_bet

        balance = currency_service_instance.get_balance(user_name)
        if balance < amount:
            return False, f"@{user_name} Zu wenig Punkte! (Benötigt: {amount})"

        with self.lock:
            currency_service_instance.add_points(user_name, -amount)

            segments = settings["segments"]
            weights = [s.get("weight", 1) for s in segments]

            # --- INDEX-BASIERTE AUSWAHL (Wichtig für Felder mit gleichen Werten) ---
            indices = range(len(segments))
            result_index = random.choices(indices, weights=weights, k=1)[0]
            result_segment = segments[result_index]
            # ---------------------------------------------------------------------

            multiplier = float(result_segment.get("value", 0))
            win_amount = int(amount * multiplier)

            pfp_url = self._get_pfp(user_name)

            self.active_spin = {
                "user": user_name,
                "pfp": pfp_url,
                "bet": amount,
                "win_amount": win_amount,
                "segments": segments,
                "target_index": result_index,
                "timestamp": time.time()
            }

            threading.Thread(target=self._finish_spin_later, args=(user_name, win_amount), daemon=True).start()
            return True, None

    def _finish_spin_later(self, user_name, win_amount):
        from services.service_provider import twitch_service_instance, currency_service_instance
        time.sleep(8)  # Wartezeit für Animation

        if win_amount > 0:
            currency_service_instance.add_points(user_name, win_amount)
            msg = f"@{user_name} Gewonnen! +{win_amount} Punkte."
        else:
            msg = f"@{user_name} Leider nichts gewonnen."

        twitch_service_instance.send_message(msg)
        time.sleep(2)
        self.active_spin = None

    def get_current_state(self):
        return self.active_spin