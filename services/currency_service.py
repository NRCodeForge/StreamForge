import sqlite3
from config import DATABASE_PATH
from utils import server_log


class CurrencyService:
    def __init__(self):
        self.settings = {}  # Wird vom SettingsManager gefüllt

    def _get_conn(self):
        return sqlite3.connect(DATABASE_PATH)

    def add_points(self, user_name, amount):
        """Fügt einem User Punkte hinzu (oder erstellt ihn)."""
        if amount == 0: return
        user_id = user_name.lower()
        try:
            with self._get_conn() as conn:
                cursor = conn.cursor()
                # Upsert Logik (Insert oder Update)
                cursor.execute("""
                               INSERT INTO currency (user_id, user_name, amount)
                               VALUES (?, ?, ?) ON CONFLICT(user_id) DO
                               UPDATE SET
                                   amount = amount + ?,
                                   user_name = ?
                               """, (user_id, user_name, amount, amount, user_name))
                conn.commit()
                # Optional: Log bei großen Mengen
                if amount > 100:
                    server_log.info(f"💰 {user_name} erhält {amount} Punkte.")
        except Exception as e:
            server_log.error(f"DB Error (add_points): {e}")

    def get_balance(self, user_name):
        """Gibt den Kontostand zurück."""
        user_id = user_name.lower()
        try:
            with self._get_conn() as conn:
                cur = conn.cursor()
                cur.execute("SELECT amount FROM currency WHERE user_id = ?", (user_id,))
                row = cur.fetchone()
                return row[0] if row else 0
        except:
            return 0

    def transfer(self, sender, recipient, amount):
        """Überweist Punkte von A nach B."""
        sender_id = sender.lower()
        recipient_id = recipient.lower()

        if amount <= 0: return False, "Betrag muss positiv sein."
        if sender_id == recipient_id: return False, "Du kannst dir nicht selbst senden."

        try:
            with self._get_conn() as conn:
                cur = conn.cursor()

                # Check Balance
                cur.execute("SELECT amount FROM currency WHERE user_id = ?", (sender_id,))
                row = cur.fetchone()
                balance = row[0] if row else 0

                if balance < amount:
                    return False, f"Nicht genug Punkte ({balance})."

                # Abziehen
                cur.execute("UPDATE currency SET amount = amount - ? WHERE user_id = ?", (amount, sender_id))

                # Gutschreiben (User erstellen falls nicht existent)
                cur.execute("""
                            INSERT INTO currency (user_id, user_name, amount)
                            VALUES (?, ?, ?) ON CONFLICT(user_id) DO
                            UPDATE SET amount = amount + ?
                            """, (recipient_id, recipient, amount, amount))

                conn.commit()
                return True, f"Erfolgreich {amount} an {recipient} gesendet."
        except Exception as e:
            server_log.error(f"Transfer Error: {e}")
            return False, "Datenbankfehler."

    def reset_all(self):
        try:
            with self._get_conn() as conn:
                conn.execute("DELETE FROM currency")
                conn.commit()
        except Exception as e:
            server_log.error(f"Reset Error: {e}")