import threading
import time
from playwright.sync_api import sync_playwright
from utils import server_log


class TikfinityClient:
    """
    Kapselt die Logik zum Abrufen des Like-Werts von einem externen Widget.
    Läuft in einem persistenten Hintergrund-Thread, um den Wert
    kontinuierlich zu überwachen, anstatt den Browser bei jeder
    Anfrage neu zu starten.
    """

    def __init__(self, widget_url):
        self.widget_url = widget_url
        self.latest_like_count = 0.0
        self.lock = threading.Lock()
        self.running = False
        self.monitor_thread = None
        # Ein Signal, dass der erste Wert geladen wurde
        self.first_value_ready = threading.Event()

    def start_monitoring(self):
        """Startet den Hintergrund-Thread, falls er noch nicht läuft."""
        if self.monitor_thread is None:
            self.running = True
            self.monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
            self.monitor_thread.start()

    def stop_monitoring(self):
        """Signalisiert dem Thread, sich zu beenden und wartet auf ihn."""
        self.running = False
        if self.monitor_thread:
            server_log.info("Warte auf Beendigung des Tikfinity-Monitor-Threads...")
            self.monitor_thread.join()
            server_log.info("Tikfinity-Monitor-Thread erfolgreich beendet.")

    def get_current_like_count(self):
        """
        Gibt den zuletzt abgerufenen Like-Zähler (Threadsicher) zurück.
        Wartet beim ersten Aufruf kurz, bis der Monitor-Thread
        einen Wert hat (max. 5 Sekunden).
        """
        # Wartet, bis der Thread "bereit" signalisiert
        # (Beim ersten Aufruf blockiert dies kurz, danach ist es sofort durch)
        self.first_value_ready.wait(timeout=5.0)
        with self.lock:
            return self.latest_like_count

    def _monitor_loop(self):
        """
        Die Hauptschleife (wird im Thread ausgeführt).
        """
        server_log.info(f"Tikfinity-Monitor-Thread gestartet für: {self.widget_url}")

        try:
            with sync_playwright() as p:
                browser = p.firefox.launch(headless=True)
                page = browser.new_page()
                page.goto(self.widget_url, wait_until="load")

                # Warten, bis die Variable initial existiert
                page.wait_for_function("window.lastPercentValue !== undefined", timeout=30000)

                # Wir loggen ohne Emoji, um den Unicode-Fehler zu vermeiden
                server_log.info("Tikfinity-Ueberwachung (Thread) ist aktiv...")

                while self.running:
                    try:
                        value = page.evaluate("window.lastPercentValue")
                        like_count = int(value)

                        if like_count != self.latest_like_count:
                            with self.lock:
                                self.latest_like_count = like_count

                        # Signalisiere dem Hauptthread, dass wir einen Wert haben.
                        self.first_value_ready.set()

                        time.sleep(0.5)  # Abfrage alle 500 ms

                    except Exception as e:
                        # Fehler bei der Seitenauswertung (z.B. Seite neu geladen)
                        server_log.error(f"Fehler in der Monitor-Schleife: {e}")
                        time.sleep(5)  # Länger warten, bevor wir es erneut versuchen

                browser.close()

        except Exception as e:
            # Schwerwiegender Fehler (z.B. Playwright konnte nicht starten)
            server_log.error(f"Schwerwiegender Fehler im Tikfinity-Thread: {e}")
            self.monitor_thread = None