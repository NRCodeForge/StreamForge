from .db_connector import get_db_connection

class WishRepository:
    def get_wishes(self, offset, limit=2):
        """Ruft eine begrenzte Anzahl von Wünschen mit Offset ab."""
        conn = get_db_connection()
        c = conn.cursor()
        c.execute("SELECT wunsch, user_name FROM killer_wuensche ORDER BY datum DESC LIMIT ? OFFSET ?",
                  (limit, offset))
        # Konvertiert sqlite3.Row Objekte in Dictionaries
        wishes = [dict(row) for row in c.fetchall()]
        conn.close()
        return wishes

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