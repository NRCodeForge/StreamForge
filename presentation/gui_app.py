import threading
import tkinter as tk
from tkinter import messagebox, font
import requests
import sys
import os

from PIL import Image, ImageTk

from presentation.ui_elements import UIElementCard, show_toast, start_hotkey_listener
from presentation.settings_windows import SubathonSettingsWindow, LikeChallengeSettingsWindow, CommandsSettingsWindow
from services.service_provider import like_service_instance

from config import Style, BASE_HOST, BASE_PORT, BASE_URL, RESET_WISHES_ENDPOINT, get_path
from utils import server_log

from presentation.web_api import app as flask_app

UI_ELEMENTS_CONFIG = [
    {"name": "Wishlist", "path": "killer_wishes/index.html", "has_settings": False, "has_reset": True},
    {"name": "Subathon Overlay", "path": "subathon_overlay/index.html", "has_settings": True,
     "settings_func_name": "open_subathon_settings_window", "has_reset": False},
    {"name": "Timer Overlay", "path": "timer_overlay/index.html", "has_settings": False, "has_reset": False},
    {"name": "Like Challenge", "path": "like_overlay/index.html", "has_settings": True,
     "settings_func_name": "open_like_challenge_settings_window", "has_reset": False},
    {"name": "Commands Overlay", "path": "commands/index.html",
     "has_settings": True,
     "settings_func_name": "open_commands_settings_window",
     "has_reset": False}
]


class StreamForgeGUI:
    """Die Haupt-GUI-Anwendung des StreamForge Managers."""

    def __init__(self):
        """Initialisiert das Hauptfenster, lädt Assets und startet Hilfs-Threads (Hotkey-Listener)."""
        self.root = tk.Tk()
        self.root.title("StreamForge Overlay Manager")
        self.root.geometry("700x640")
        self.root.resizable(False, False)
        self.root.configure(bg=Style.BACKGROUND)

        # Pfad zum Icon (im Hauptverzeichnis des Projekts)
        icon_path = get_path("assets/icon.ico")
        if os.path.exists(icon_path):
            try:
                self.root.iconbitmap(icon_path)
            except tk.TclError as e:
                server_log.error(
                    f"Fehler beim Setzen des Fenster-Icons (TclError, möglicherweise falsches Format): {e}")
            except Exception as e:
                server_log.error(f"Unbekannter Fehler beim Setzen des Fenster-Icons: {e}")
        else:
            server_log.warning(f"Fenster-Icon-Datei nicht gefunden: {icon_path}")

        # State: Ein Array, dessen Wert im Hotkey-Listener (separater Thread) aktualisiert werden kann
        self.is_server_running = [False]
        self.flask_thread = None

        self.setup_ui()
        self.setup_callbacks()

        # Starte Hotkey-Listener in einem Daemon-Thread
        start_hotkey_listener(self.is_server_running)

    def setup_ui(self):
        """Erzeugt alle UI-Elemente (Statuszeile, Karten, Hotkey-Hinweis, Logo)."""
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
            settings_func = None
            func_name = config.get("settings_func_name")

            if func_name:
                settings_func = getattr(self, func_name, None)

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
        tk.Label(hotkey_frame, text="Hotkey: Drücke 'Bild Runter'\n für den nächsten Wunsch",
                 font=font.Font(family=Style.FONT_FAMILY, size=11, slant="italic"), bg=Style.BACKGROUND,
                 fg=Style.TEXT_MUTED).pack()

        # --- Logo mit proportionaler Skalierung ---
        logo_path = get_path("assets/LOGO.png")
        if os.path.exists(logo_path):
            try:
                pil_image = Image.open(logo_path)
                base_width = 150
                w_percent = (base_width / float(pil_image.size[0]))
                h_size = int((float(pil_image.size[1]) * float(w_percent)))

                pil_image_resized = pil_image.resize((base_width, h_size), Image.Resampling.LANCZOS)
                self.logo_image = ImageTk.PhotoImage(pil_image_resized)

                logo_label = tk.Label(self.root, image=self.logo_image, bg=Style.BACKGROUND)
                logo_label.place(relx=1.0, rely=1.0, x=-10, y=-10, anchor="se")

            except Exception as e:
                server_log.error(f"Fehler beim Laden oder Skalieren des Logos: {e}")
        else:
            server_log.warning(f"Logo-Datei nicht gefunden: {logo_path}")

    def setup_callbacks(self):
        """Bindet Fenster-Ereignisse (z. B. Schließen) an passende Handler."""
        self.root.protocol("WM_DELETE_WINDOW", self.on_app_close)

    # --- Server Management ---
    def start_webserver(self):
        """Startet den Flask-Webserver in einem Hintergrund-Thread und aktualisiert den Status in der GUI."""
        if self.is_server_running[0]:
            return

        def run_flask():
            try:
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
        """Fährt Hintergrunddienste sauber herunter und beendet die Anwendung."""
        if like_service_instance.client:
            server_log.info("Stoppe Tikfinity-Monitor...")
            like_service_instance.client.stop_monitoring()

        self.is_server_running[0] = False
        server_log.info("Anwendung StreamForge geschlossen.")
        self.root.destroy()

    def reset_database_action(self):
        """Setzt die Wunsch-Datenbank über die API zurück (bestätigungsbasiert)."""
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

    def open_subathon_settings_window(self):
        """Öffnet das Einstellungsfenster für den Subathon-Overlay."""
        SubathonSettingsWindow(self.root)

    def open_like_challenge_settings_window(self):
        """Öffnet das Einstellungsfenster für die Like-Challenge."""
        LikeChallengeSettingsWindow(self.root)

    def open_commands_settings_window(self):
        CommandsSettingsWindow(self.root)

    def update_status(self, message, color):
        """Aktualisiert die Statuszeile in der GUI mit Text und Farbe."""
        self.status_label.config(text=message, fg=color)

    def start(self):
        """Initialisiert Datenbankabhängigkeiten, startet den Webserver und öffnet die GUI-Hauptschleife."""
        from database.db_setup import setup_database
        setup_database()

        self.root.after(100, self.start_webserver)
        self.root.mainloop()