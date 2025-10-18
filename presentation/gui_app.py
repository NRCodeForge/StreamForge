import threading
import tkinter as tk
from tkinter import messagebox, font
import requests
import sys

# Importiere Komponenten aus der Präsentation und dem Service Layer
from presentation.ui_elements import UIElementCard, show_toast, start_hotkey_listener
from presentation.settings_windows import SubathonSettingsWindow, LikeChallengeSettingsWindow
from services.wish_service import WishService

# Importiere Infrastruktur
from ..config import Style, BASE_HOST, BASE_PORT, BASE_URL, RESET_WISHES_ENDPOINT
from ..utils import server_log

# Importiere die Flask-App, um sie in einem Thread zu starten
# (api.py muss in einem separaten Schritt existieren)
from .api import app as flask_app

# Globale Konfiguration für die UI-Elemente
UI_ELEMENTS_CONFIG = [
    {"name": "Wishlist", "path": "killer_wishes/index.html", "has_settings": False, "has_reset": True},
    {"name": "Subathon Overlay", "path": "subathon_overlay/index.html", "has_settings": True,
     "settings_func_name": "open_subathon_settings_window", "has_reset": False},
    {"name": "Timer Overlay", "path": "timer_overlay/index.html", "has_settings": False, "has_reset": False},
    {"name": "Like Challenge", "path": "like_overlay/index.html", "has_settings": True,
     "settings_func_name": "open_like_challenge_settings_window", "has_reset": False}
]


class StreamForgeGUI:
    """Die Haupt-GUI-Anwendung des StreamForge Managers."""

    def __init__(self):
        self.root = tk.Tk()
        self.root.title("StreamForge Overlay Manager")
        self.root.geometry("600x520")
        self.root.resizable(False, False)
        self.root.configure(bg=Style.BACKGROUND)

        # State: Ein Array, dessen Wert im Hotkey-Listener (separater Thread) aktualisiert werden kann
        self.is_server_running = [False]
        self.flask_thread = None

        self.setup_ui()
        self.setup_callbacks()

        # Starte Hotkey-Listener in einem Daemon-Thread
        start_hotkey_listener(self.is_server_running)

    def setup_ui(self):
        # --- Status Frame ---
        server_frame = tk.Frame(self.root, bg=Style.BACKGROUND)
        server_frame.pack(pady=(20, 10), padx=20, fill=tk.X)
        tk.Label(server_frame, text="Serverstatus:", font=font.Font(family=Style.FONT_FAMILY, size=20, weight="bold"),
                 bg=Style.BACKGROUND,
                 fg=Style.FOREGROUND).pack(side=tk.LEFT, padx=(0, 10))
        self.status_label = tk.Label(server_frame, text="Server: OFFLINE", fg=Style.DANGER,
                                     font=font.Font(family=Style.FONT_FAMILY, size=20, weight="bold"),
                                     bg=Style.BACKGROUND)
        self.status_label.pack(side=tk.LEFT)

        separator1 = tk.Frame(self.root, height=2, bg=Style.BORDER)
        separator1.pack(fill=tk.X, padx=50, pady=(10, 20))

        # --- Element Manager Frame ---
        element_manager_frame = tk.Frame(self.root, bg=Style.BACKGROUND)
        element_manager_frame.pack(pady=10, padx=30, fill=tk.X)

        for config in UI_ELEMENTS_CONFIG:
            # Holen der Funktionen über getattr, da sie Methoden der GUI-Klasse sind
            settings_func = getattr(self, config.get("settings_func_name"), None)
            reset_func = self.reset_database_action if config.get("has_reset") else None

            card = UIElementCard(parent=element_manager_frame, name=config["name"], path=config["path"],
                                 has_settings=config.get("has_settings", False),
                                 has_reset=config.get("has_reset", False),
                                 settings_func=settings_func,
                                 reset_func=reset_func)
            card.pack(fill=tk.X, pady=6)

        # --- Hotkey Info ---
        hotkey_frame = tk.Frame(self.root, bg=Style.BACKGROUND)
        hotkey_frame.pack(side=tk.BOTTOM, fill=tk.X, pady=20)
        tk.Label(hotkey_frame, text="Hotkey: Drücke 'Bild Runter' für den nächsten Wunsch",
                 font=font.Font(family=Style.FONT_FAMILY, size=11, slant="italic"), bg=Style.BACKGROUND,
                 fg=Style.TEXT_MUTED).pack()

    def setup_callbacks(self):
        self.root.protocol("WM_DELETE_WINDOW", self.on_app_close)

    # --- Server Management ---
    def start_webserver(self):
        if self.is_server_running[0]:
            return

        def run_flask():
            try:
                # Startet den Flask-Server
                flask_app.run(host=BASE_HOST, port=BASE_PORT, debug=False, use_reloader=False)
            except Exception as e:
                server_log.error(f"Flask Webserver crashed: {e}")
                self.update_status("Server: FEHLER", Style.DANGER)

        self.flask_thread = threading.Thread(target=run_flask, daemon=True)
        self.flask_thread.start()
        self.is_server_running[0] = True
        self.update_status("Server: ONLINE", Style.SUCCESS)
        server_log.info("Webserver erfolgreich gestartet.")

    def on_app_close(self):
        self.is_server_running[0] = False
        server_log.info("Anwendung StreamForge geschlossen.")
        self.root.destroy()

    # --- Action Callbacks (Interaktion mit dem Service Layer über HTTP) ---
    def reset_database_action(self):
        """Sendet einen HTTP POST Request zum Zurücksetzen der Datenbank (WishService)."""
        if not self.is_server_running[0]:
            messagebox.showerror("Fehler", "Server ist nicht aktiv.")
            return

        if messagebox.askyesno("Bestätigen",
                               "Bist du sicher, dass du alle Killer-Wünsche unwiderruflich löschen möchtest?"):
            try:
                response = requests.post(BASE_URL.rstrip('/') + RESET_WISHES_ENDPOINT)
                response.raise_for_status()
                show_toast(self.root, "Datenbank zurückgesetzt")
            except requests.exceptions.RequestException as e:
                messagebox.showerror("Fehler", f"Serverfehler beim Zurücksetzen: {e}")

    # --- Settings Window Callbacks ---
    def open_subathon_settings_window(self):
        SubathonSettingsWindow(self.root)

    def open_like_challenge_settings_window(self):
        LikeChallengeSettingsWindow(self.root)

    def update_status(self, message, color):
        self.status_label.config(text=message, fg=color)

    def start(self):
        # Stellt sicher, dass die Datenbank-Struktur existiert, bevor der Server startet
        from database.db_setup import setup_database
        setup_database()

        # Startet Server nach kurzer Verzögerung, um die GUI zu laden
        self.root.after(100, self.start_webserver)
        self.root.mainloop()