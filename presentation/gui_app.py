import threading
import tkinter as tk
from tkinter import messagebox, font, Toplevel
import requests
import sys
import os
import random
from PIL import Image, ImageTk

# Importiere Services und Config
from presentation.settings_windows import SubathonSettingsWindow, LikeChallengeSettingsWindow, CommandsSettingsWindow
from services.service_provider import like_service_instance

from config import (
    Style, BASE_HOST, BASE_PORT, BASE_URL,
    RESET_WISHES_ENDPOINT, WISHES_ENDPOINT,
    get_path, COMMANDS_TRIGGER_ENDPOINT
)
from utils import server_log
from presentation.web_api import app as flask_app
from presentation.ui_elements import show_toast, start_hotkey_listener

# --- TEXTE FÜR INFO SCREENS ---
INFO_TEXTS = {
    "LIKES": "LIKE SYSTEM\n\nAutomatische Like-Challenge & Progress Bar.",
    "TIMER": "TIMER & SUBATHON\n\nZeitsteuerung für Events und Countdowns.",
    "WISHES": "KILLER WISHES\n\nZuschauer-Wunschliste für Killer/Survivor.",
    "COMMANDS": "COMMAND OVERLAY\n\nGroße Medien-Einblendungen triggern."
}


class DashboardCard(tk.Frame):
    """Ein einheitliches Modul für das Grid-Layout."""

    def __init__(self, parent, title, items, settings_func=None, test_func=None, reset_func=None, info_key=None,
                 test_label="TEST"):
        # Dunkler Hintergrund für modernen Look
        card_bg = "#1a1a1a"

        super().__init__(parent, bg=card_bg, highlightbackground=Style.BORDER, highlightthickness=1)
        self.parent_root = parent.winfo_toplevel()
        self.info_key = info_key

        # FESTE GRÖSSE für einheitliches Raster
        self.config(width=280, height=220)
        self.pack_propagate(False)

        # --- HEADER ---
        header = tk.Frame(self, bg=card_bg)
        header.pack(fill=tk.X, padx=12, pady=(12, 5))

        tk.Label(header, text=title, font=font.Font(family=Style.FONT_FAMILY, size=12, weight="bold"),
                 bg=card_bg, fg=Style.ACCENT_BLUE).pack(side=tk.LEFT)

        # Icons rechts
        btn_frame = tk.Frame(header, bg=card_bg)
        btn_frame.pack(side=tk.RIGHT)

        if settings_func: self._add_icon(btn_frame, "⚙", settings_func, card_bg)
        if reset_func: self._add_icon(btn_frame, "🗑", reset_func, card_bg, color=Style.DANGER)
        if info_key: self._add_icon(btn_frame, "ℹ", self.show_info, card_bg, font=("Arial", 11, "italic"))

        # --- CONTENT ---
        content = tk.Frame(self, bg=card_bg)
        content.pack(fill=tk.BOTH, expand=True, padx=15, pady=5)

        for name, path in items:
            row = tk.Frame(content, bg=card_bg)
            row.pack(fill=tk.X, pady=4)

            tk.Label(row, text=name, font=("Segoe UI", 10), bg=card_bg, fg="#cccccc").pack(side=tk.LEFT)

            url = BASE_URL.rstrip('/') + '/' + path.lstrip('/')
            tk.Button(row, text="❐", command=lambda u=url: self.copy_to_clipboard(u),
                      bg=card_bg, fg=Style.ACCENT_PURPLE, relief=tk.FLAT, bd=0, cursor="hand2").pack(side=tk.RIGHT)

        # --- FOOTER ---
        if test_func:
            tk.Button(self, text=f"▶ {test_label}", command=test_func,
                      bg=Style.ACCENT_PURPLE, fg="white", relief=tk.FLAT,
                      font=("Arial", 9, "bold"), cursor="hand2").pack(fill=tk.X, side=tk.BOTTOM, padx=15, pady=15)

    def _add_icon(self, parent, text, cmd, bg_col, color="#888888", font=("Arial", 12)):
        btn = tk.Button(parent, text=text, command=cmd, bg=bg_col, fg=color,
                        relief=tk.FLAT, bd=0, font=font, width=3, cursor="hand2")
        btn.pack(side=tk.LEFT)
        btn.bind("<Enter>", lambda e: btn.config(fg="white"))
        btn.bind("<Leave>", lambda e: btn.config(fg=color))

    def copy_to_clipboard(self, text):
        self.parent_root.clipboard_clear()
        self.parent_root.clipboard_append(text)
        show_toast(self.parent_root, "Link kopiert!")

    def show_info(self):
        messagebox.showinfo("Info", INFO_TEXTS.get(self.info_key, ""))


class StreamForgeGUI:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("StreamForge Manager")

        # Standard: Maximiert starten
        try:
            self.root.state('zoomed')
        except:
            self.root.geometry("1200x800")

        self.root.configure(bg=Style.BACKGROUND)
        self.root.minsize(800, 600)

        icon_path = get_path("assets/icon.ico")
        if os.path.exists(icon_path):
            try:
                self.root.iconbitmap(icon_path)
            except:
                pass

        self.is_server_running = [False]
        self.cards = []
        self.card_windows = []

        # Bilder speichern um Garbage Collection zu verhindern
        self.images = {}

        self.setup_ui()
        self.setup_callbacks()
        start_hotkey_listener(self.is_server_running)

    def setup_ui(self):
        logo_path = get_path("assets/LOGO.png")

        # --- 1. HEADER (Top) ---
        header = tk.Frame(self.root, bg=Style.BACKGROUND)
        header.pack(fill=tk.X, side=tk.TOP, padx=30, pady=20)

        # Header Icon laden
        if os.path.exists(logo_path):
            try:
                pil_icon = Image.open(logo_path).convert("RGBA")
                pil_icon.thumbnail((240, 135), Image.Resampling.LANCZOS)
                self.images['header_icon'] = ImageTk.PhotoImage(pil_icon)
                tk.Label(header, image=self.images['header_icon'], bg=Style.BACKGROUND).pack(side=tk.LEFT, padx=(0, 15))
            except:
                pass

        # Titel
        tk.Label(header, text="STREAMFORGE", font=("Impact", 32),
                 bg=Style.BACKGROUND, fg=Style.FOREGROUND).pack(side=tk.LEFT)

        # Controls (Rechts)
        controls = tk.Frame(header, bg=Style.BACKGROUND)
        controls.pack(side=tk.RIGHT)

        tk.Button(controls, text="👤", command=self.open_global_settings,
                  bg=Style.BACKGROUND, fg=Style.ACCENT_BLUE, relief=tk.FLAT,
                  font=("Arial", 20), bd=0, cursor="hand2").pack(side=tk.LEFT, padx=20)

        self.status_canvas = tk.Canvas(controls, width=18, height=18, bg=Style.BACKGROUND, highlightthickness=0)
        self.status_canvas.pack(side=tk.LEFT)
        self.status_indicator = self.status_canvas.create_oval(2, 2, 16, 16, fill=Style.DANGER, outline="")

        # --- 2. FOOTER (Bottom) ---
        footer = tk.Frame(self.root, bg="#111111", height=40)
        footer.pack(fill=tk.X, side=tk.BOTTOM)

        f_content = tk.Frame(footer, bg="#111111")
        f_content.pack(fill=tk.BOTH, padx=20, pady=8)

        # Links: Version & Slogan
        tk.Label(f_content, text="v2.0  |  FORGED FOR STREAMERS", font=("Segoe UI", 10, "bold"),
                 bg="#111111", fg="#666666").pack(side=tk.LEFT)

        # Rechts: Logo & Credit
        f_right = tk.Frame(f_content, bg="#111111")
        f_right.pack(side=tk.RIGHT)
        icon_path = get_path("assets/icon.ico")
        if os.path.exists(icon_path):
            try:
                pil_f = Image.open(icon_path).convert("RGBA")
                pil_f.thumbnail((100,100), Image.Resampling.LANCZOS)
                self.images['footer_logo'] = ImageTk.PhotoImage(pil_f)
                tk.Label(f_right, image=self.images['footer_logo'], bg="#111111").pack(side=tk.RIGHT, padx=(10, 0))
            except:
                pass

        tk.Label(f_right, text="STREAMFORGE SYSTEM", font=("Segoe UI", 9), bg="#111111", fg="#444444").pack(
            side=tk.RIGHT)

        # --- 3. MAIN AREA (Scrollbar + Canvas) ---
        main_frame = tk.Frame(self.root, bg=Style.BACKGROUND)
        main_frame.pack(fill=tk.BOTH, expand=True)

        self.canvas = tk.Canvas(main_frame, bg=Style.BACKGROUND, highlightthickness=0)

        # Scrollbar Design
        self.scrollbar = tk.Scrollbar(main_frame, orient="vertical", command=self.canvas.yview)
        self.canvas.configure(yscrollcommand=self.scrollbar.set)

        self.scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self.canvas.bind_all("<MouseWheel>", self._on_mousewheel)

        # --- MODULE HINZUFÜGEN ---
        self.cards.append(DashboardCard(
            self.canvas, "LIKES",
            [("Challenge Text", "like_overlay/index.html"), ("Progress Bar", "like_progress_bar/index.html")],
            settings_func=self.open_like_challenge_settings_window,
            test_func=self.test_likes_action, test_label="TEST +100",
            info_key="LIKES"
        ))

        self.cards.append(DashboardCard(
            self.canvas, "TIMER & SUBATHON",
            [("Subathon", "subathon_overlay/index.html"), ("Timer", "timer_overlay/index.html")],
            settings_func=self.open_subathon_settings_window,
            info_key="TIMER"
        ))

        self.cards.append(DashboardCard(
            self.canvas, "KILLER WISHES",
            [("Wishlist Overlay", "killer_wishes/index.html")],
            reset_func=self.reset_database_action,
            test_func=self.test_wish_action, test_label="WUNSCH +1",
            info_key="WISHES"
        ))

        self.cards.append(DashboardCard(
            self.canvas, "COMMANDS",
            [("Media Overlay", "commands/index.html")],
            settings_func=self.open_commands_settings_window,
            test_func=self.test_command_action, test_label="FIRE SEQUENZ",
            info_key="COMMANDS"
        ))

        self.canvas.bind("<Configure>", self.on_resize)

    def on_resize(self, event):
        """Responsive Grid Positionierung."""
        w = event.width

        card_w = 280
        card_h = 220
        gap_x = 25
        gap_y = 25

        # Grid Berechnung
        cols = max(1, (w - gap_x) // (card_w + gap_x))
        total_grid_w = cols * card_w + (cols - 1) * gap_x
        start_x = (w - total_grid_w) // 2
        start_y = 30

        # Karten platzieren
        if not self.card_windows:
            for card in self.cards:
                win = self.canvas.create_window(0, 0, window=card, anchor="nw")
                self.card_windows.append(win)

        rows = 0
        for i, win_id in enumerate(self.card_windows):
            col_idx = i % cols
            row_idx = i // cols
            rows = row_idx + 1
            x = start_x + col_idx * (card_w + gap_x)
            y = start_y + row_idx * (card_h + gap_y)
            self.canvas.coords(win_id, x, y)

        # Scrollbereich anpassen
        total_h = start_y + rows * (card_h + gap_y) + 50
        self.canvas.configure(scrollregion=(0, 0, w, total_h))

        # Hintergrund-Logo wurde entfernt.

    def _on_mousewheel(self, event):
        self.canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

    # --- ACTIONS ---
    def test_likes_action(self):
        if self.is_server_running[0]:
            try:
                requests.post(f"http://{BASE_HOST}:{BASE_PORT}/api/v1/like_challenge/test", timeout=0.1)
            except:
                pass
            show_toast(self.root, "100 Likes gesendet!")

    def test_wish_action(self):
        if self.is_server_running[0]:
            k = ["Trapper", "Wraith", "Billy", "Nurse", "Huntress", "Myers", "Hag", "Doctor"]
            try:
                requests.post(BASE_URL.rstrip('/') + WISHES_ENDPOINT,
                              json={"wunsch": random.choice(k), "user_name": "TestUser"}, timeout=0.1)
            except:
                pass
            show_toast(self.root, "Wunsch hinzugefügt!")

    def test_command_action(self):
        from config import COMMANDS_TRIGGER_ENDPOINT
        if self.is_server_running[0]:
            try:
                requests.post(BASE_URL.rstrip('/') + COMMANDS_TRIGGER_ENDPOINT, timeout=0.1)
            except:
                pass
            show_toast(self.root, "Sequenz gestartet!")

    def reset_database_action(self):
        if not self.is_server_running[0]: return
        if messagebox.askyesno("Reset", "Alle Wünsche löschen?"):
            try:
                requests.post(BASE_URL.rstrip('/') + RESET_WISHES_ENDPOINT, timeout=0.1)
            except:
                pass
            show_toast(self.root, "Datenbank geleert")

    def open_global_settings(self):
        GlobalSettingsWindow(self.root)

    def open_subathon_settings_window(self):
        SubathonSettingsWindow(self.root)

    def open_like_challenge_settings_window(self):
        LikeChallengeSettingsWindow(self.root)

    def open_commands_settings_window(self):
        CommandsSettingsWindow(self.root)

    def start_webserver(self):
        if self.is_server_running[0]: return

        def r():
            try:
                flask_app.run(host=BASE_HOST, port=BASE_PORT, debug=False, use_reloader=False)
            except:
                self.status_canvas.itemconfig(self.status_indicator, fill=Style.DANGER)

        self.flask_thread = threading.Thread(target=r, daemon=True)
        self.flask_thread.start()
        self.is_server_running[0] = True
        self.status_canvas.itemconfig(self.status_indicator, fill=Style.SUCCESS)

    def setup_callbacks(self):
        self.root.protocol("WM_DELETE_WINDOW", self.on_app_close)

    def on_app_close(self):
        if hasattr(like_service_instance, 'api_client') and like_service_instance.api_client:
            try:
                like_service_instance.api_client.stop()
            except:
                pass
        self.is_server_running[0] = False
        self.root.destroy()
        sys.exit(0)

    def start(self):
        from database.db_setup import setup_database
        setup_database()
        self.root.after(100, self.start_webserver)
        self.root.mainloop()


class GlobalSettingsWindow(tk.Toplevel):
    def __init__(self, master):
        super().__init__(master)
        self.title("Settings")
        self.geometry("400x220")
        self.configure(bg=Style.BACKGROUND)
        x = master.winfo_x() + 100;
        y = master.winfo_y() + 100
        self.geometry(f"+{x}+{y}")

        tk.Label(self, text="TikTok Username (ohne @):", bg=Style.BACKGROUND, fg=Style.FOREGROUND,
                 font=("Arial", 12)).pack(pady=(40, 5))
        self.uv = tk.StringVar()
        try:
            self.uv.set(like_service_instance.settings_manager.load_settings().get("tiktok_unique_id", ""))
        except:
            pass
        tk.Entry(self, textvariable=self.uv, font=("Arial", 12), bg="#333333", fg="white", insertbackground="white",
                 relief=tk.FLAT).pack(pady=5, padx=40, fill=tk.X, ipady=3)
        tk.Button(self, text="SPEICHERN", command=self.save, bg=Style.ACCENT_PURPLE, fg="white", relief=tk.FLAT,
                  font=("Arial", 10, "bold")).pack(pady=20, ipadx=20)

    def save(self):
        v = self.uv.get().strip()
        if v:
            s = like_service_instance.settings_manager.load_settings()
            s["tiktok_unique_id"] = v
            like_service_instance.settings_manager.save_settings(s)
            show_toast(self.master, "Gespeichert")
            self.destroy()