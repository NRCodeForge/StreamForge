from playwright.sync_api import sync_playwright
# KORREKTUR: Verwende absoluten Import
from utils import server_log


class TikfinityClient:
    """Kapselt die Logik zum Abrufen des Like-Werts von einem externen Widget (Playwright)."""

    def fetch_like_count(self, widget_url):
        """
        Navigiert zur Widget-URL und extrahiert den Like-Wert mittels Playwright.
        (Logik aus app.py übernommen)
        """
        if not widget_url:
            raise ValueError("widgetUrl darf nicht leer sein.")

        server_log.info(f"Starte Playwright, um Like-Zähler von {widget_url} abzurufen...")

        try:
            with sync_playwright() as p:
                browser = p.firefox.launch(headless=True)
                page = browser.new_page()
                page.goto(widget_url, wait_until="domcontentloaded", timeout=30000)

                page.wait_for_function("window.lastPercentValue !== undefined", timeout=10000)

                value = page.evaluate("window.lastPercentValue")
                browser.close()

            if value is None:
                raise ValueError("Die Variable 'window.lastPercentValue' wurde im Widget nicht gefunden.")

            # Die Umrechnung aus dem Originalcode (value / 10)
            return float(value) / 10

        except Exception as e:
            server_log.error(f"Fehler bei Playwright/Tikfinity-Abruf: {e}")
            raise ValueError(f"Fehler beim Abrufen des Like-Zählers: {e}")