# Tikfinity-Client: Überwacht die Like-Werte eines externen Widgets in einem Hintergrund-Thread.

import threading
import time
from playwright.sync_api import sync_playwright
from utils import server_log
import os
import glob
import sys # <-- Hinzufügen für sys.frozen Check
# Stelle sicher, dass get_path aus der korrigierten config.py importiert wird
from config import get_path


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

        # --- Pfad zur gebündelten Firefox-Executable bestimmen ---
        bundled_executable_path = None
        try:
            # get_path('.') gibt das Verzeichnis der EXE zurück (oder des Skripts)
            base_dir = get_path('.')
            ms_playwright_dir = os.path.join(base_dir, 'ms-playwright')
            server_log.info(f"Suche nach ms-playwright in: {ms_playwright_dir}") # Debugging Log

            if os.path.isdir(ms_playwright_dir):
                # Finde den firefox-<versionsnummer> Ordner
                firefox_version_dirs = glob.glob(os.path.join(ms_playwright_dir, 'firefox-*'))
                if firefox_version_dirs:
                    # Nimm den ersten gefundenen Versionsordner
                    # Konstruiere den Pfad zur firefox.exe
                    firefox_exe_path = os.path.join(firefox_version_dirs[0], 'firefox', 'firefox.exe')
                    # Normalisiere den Pfad (korrigiert Slashes)
                    firefox_exe_path = os.path.normpath(firefox_exe_path)

                    if os.path.isfile(firefox_exe_path):
                        bundled_executable_path = firefox_exe_path
                        server_log.info(f"Verwende gebündelte Firefox-Executable: {bundled_executable_path}")
                    else:
                        server_log.error(f"Firefox-Verzeichnis gefunden, aber firefox.exe fehlt unter dem erwarteten Pfad: {firefox_exe_path}")
                else:
                    server_log.error(f"Konnte firefox-* Verzeichnis nicht in {ms_playwright_dir} finden.")
            else:
                 # Nur loggen, wenn wir GEBUNDELT sind, sonst ist das normal
                 if getattr(sys, 'frozen', False):
                     server_log.warning(f"Gebündeltes ms-playwright Verzeichnis nicht gefunden: {ms_playwright_dir}. Playwright versucht Standardpfad.")

        except Exception as find_path_e:
            server_log.error(f"Fehler beim Bestimmen des gebündelten Firefox-Pfads: {find_path_e}")
        # --- Ende Pfad-Bestimmung ---


        try:
            with sync_playwright() as p:
                # --- executable_path übergeben ---
                server_log.info(f"Starte Firefox mit executable_path='{bundled_executable_path}'") # Debugging Log
                browser = p.firefox.launch(
                    headless=True,
                    executable_path=bundled_executable_path # Kann None sein, dann versucht Playwright den Standardpfad
                )
                # --- Ende Änderung ---

                page = browser.new_page()
                page.goto(self.widget_url, wait_until="load")

                # Warten, bis die Variable initial existiert
                page.wait_for_function("window.lastPercentValue !== undefined", timeout=30000)

                server_log.info("Tikfinity-Ueberwachung (Thread) ist aktiv...")

                while self.running:
                    try:
                        value = page.evaluate("window.lastPercentValue")
                        # Versuche sicher in int umzuwandeln
                        try:
                            like_count = int(float(value)) # Erst float, dann int, falls es "100.0" ist
                        except (ValueError, TypeError):
                             server_log.warning(f"Konnte Wert '{value}' nicht in Zahl umwandeln.")
                             time.sleep(1) # Kurz warten und erneut versuchen
                             continue


                        if like_count != self.latest_like_count:
                            with self.lock:
                                self.latest_like_count = like_count
                            # Signalisiere dem Hauptthread, dass wir einen (neuen) Wert haben.
                            self.first_value_ready.set()
                        elif not self.first_value_ready.is_set():
                            # Signalisiere auch beim ersten Mal, selbst wenn der Wert 0 ist
                            self.first_value_ready.set()


                        time.sleep(0.5)  # Abfrage alle 500 ms

                    except Exception as loop_e:
                        server_log.error(f"Fehler in der Monitor-Schleife: {loop_e}")
                        # Prüfen ob der Browser noch verbunden ist
                        if not browser.is_connected():
                            server_log.error("Browser-Verbindung verloren. Beende Monitor-Thread.")
                            self.running = False # Thread beenden signalisieren
                            break # Innere Schleife verlassen
                        time.sleep(5)  # Länger warten, bevor wir es erneut versuchen

                # Stelle sicher, dass der Browser geschlossen wird, wenn die Schleife endet (durch self.running=False oder Fehler)
                try:
                    if browser.is_connected():
                        browser.close()
                        server_log.info("Playwright-Browser erfolgreich geschlossen.")
                except Exception as close_e:
                    server_log.warning(f"Fehler beim Schließen des Playwright-Browsers: {close_e}")


        except Exception as e:
            server_log.error(f"Schwerwiegender Fehler im Tikfinity-Thread: {e}")
            # Optional: Signalisiere, dass der erste Wert nie kam, falls noch nicht geschehen
            if not self.first_value_ready.is_set():
                 self.first_value_ready.set() # Verhindert ewiges Warten im Hauptthread

        finally:
            # Sicherstellen, dass der Thread als nicht mehr laufend markiert wird, wenn er endet
            self.running = False
            server_log.info("Tikfinity-Monitor-Thread beendet.")
            # Wichtig: Setze monitor_thread auf None, damit er bei Bedarf neu gestartet werden kann
            # Dies sollte jedoch im Hauptthread geschehen, nicht hier im Thread selbst.
            # Der Hauptthread kann prüfen, ob der Thread noch lebt und ggf. neu starten.