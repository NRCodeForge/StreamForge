from .db_connector import get_db_connection


class WishRepository:
    """Isoliert den direkten Datenbankzugriff für Killerwünsche."""

    def get_wishes(self, offset, limit=2):
        """Ruft eine begrenzte Anzahl von Wünschen mit Offset ab."""
        conn = get_db_connection()
        c = conn.cursor()
        c.execute("SELECT wunsch, user_name FROM killer_wuensche ORDER BY datum ASC LIMIT ? OFFSET ?",
                  (limit, offset))
        wuensche = [dict(row) for row in c.fetchall()]
        conn.close()
        return wuensche

    def count_total_wishes(self):
        """Zählt die Gesamtzahl der Wünsche."""
        conn = get_db_connection()
        c = conn.cursor()
        c.execute("SELECT COUNT(*) FROM killer_wuensche")
        total = c.fetchone()[0]
        conn.close()
        return total

    def add_wish(self, wunsch, user_name):
        """Fügt einen neuen Wunsch in die Datenbank ein."""
        conn = get_db_connection()
        c = conn.cursor()
        c.execute("INSERT INTO killer_wuensche (wunsch, user_name) VALUES (?, ?)", (wunsch, user_name))
        conn.commit()
        conn.close()

    def delete_all_wishes(self):
        """Löscht alle Wünsche aus der Datenbank."""
        conn = get_db_connection()
        c = conn.cursor()
        c.execute("DELETE FROM killer_wuensche")
        conn.commit()
        conn.close()

    def delete_oldest_wish(self):
        """Löscht den ältesten Wunsch (den mit der niedrigsten ID) aus der Datenbank."""
        conn = get_db_connection()
        c = conn.cursor()
        try:
            # Finde die niedrigste ID
            c.execute("SELECT MIN(id) FROM killer_wuensche")
            result = c.fetchone()
            if result and result[0] is not None:
                oldest_id = result[0]
                # Lösche den Eintrag mit dieser ID
                c.execute("DELETE FROM killer_wuensche WHERE id = ?", (oldest_id,))
                conn.commit()
                wishes_log.info(f"Ältester Wunsch mit ID {oldest_id} gelöscht.")  # Optional: Loggen
            else:
                # Optional: Loggen, wenn keine Wünsche vorhanden sind
                wishes_log.info("Keine Wünsche zum Löschen vorhanden.")
        except Exception as e:
            wishes_log.error(f"Fehler beim Löschen des ältesten Wunsches: {e}")  # Logge Fehler
            conn.rollback()  # Mache Änderungen rückgängig bei Fehler
        finally:
            conn.close()