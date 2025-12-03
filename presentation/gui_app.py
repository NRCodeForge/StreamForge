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
    "LIKES": (
        "LIKE SYSTEM\n\n"
        "Steuert die Like-Challenge & Progress-Bar.\n"
        "Verbindet automatisch zu TikTok.\n"
        "Test: Sendet 100 Fake-Likes zum Testen der Animation."
    ),
    "TIMER": (
        "TIMER & SUBATHON\n\n"
        "Subathon: Zeit läuft ab/auf bei Events.\n"
        "Timer: Einfaches Countdown-Overlay.\n"
        "Gambit: Startet das 'Russisch Roulette' Event."
    ),
    "WISHES": (
        "KILLER WISHES\n\n"
        "Wünsche für Killer/Survivor.\n"
        "Hotkey 'Bild Runter': Nächster Wunsch.\n"
        "!place NAME: Zeigt Platzierung im Overlay."
    ),
    "COMMANDS": (
        "COMMAND OVERLAY\n\n"
        "Zeigt große Medien-Overlays (Bilder/GIFs) an."
    )
}


class DashboardCard(tk.Frame):
    """
    Einheitliches Modul für das Grid-Layout.
    """

    def __init__(self, parent, title, items, settings_func=None, test_func=None, reset_func=None, info_key=None,
                 test_label="TEST", custom_buttons=None):
        card_bg = "#1a1a1a"
        super().__init__(parent, bg=card_bg, highlightbackground=Style.BORDER, highlightthickness=1)
        self.parent_root = parent.winfo_toplevel()
        self.info_key = info_key
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
        footer_frame = tk.Frame(self, bg=card_bg)
        footer_frame.pack(side=tk.BOTTOM, fill=tk.X, padx=15, pady=15)

        if custom_buttons:
            for btn_text, btn_cmd, btn_col in custom_buttons:
                tk.Button(footer_frame, text=btn_text, command=btn_cmd,
                          bg=btn_col, fg="white", relief=tk.FLAT,
                          font=("Arial", 8, "bold"), width=6).pack(side=tk.LEFT, padx=2, expand=True, fill=tk.X)
        elif test_func:
            tk.Button(footer_frame, text=f"▶ {test_label}", command=test_func,
                      bg=Style.ACCENT_PURPLE, fg="white", relief=tk.FLAT,
                      font=("Arial", 9, "bold"), cursor="hand2").pack(fill=tk.X)

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
        info_win = tk.Toplevel(self.parent_root)
        info_win.title("Information")
        info_win.geometry("400x320")
        info_win.configure(bg=Style.BACKGROUND)
        x = self.parent_root.winfo_x() + (self.parent_root.winfo_width() // 2) - 200
        y = self.parent_root.winfo_y() + (self.parent_root.winfo_height() // 2) - 160
        info_win.geometry(f"+{x}+{y}")
        tk.Label(info_win, text="INFO", font=("Impact", 22),
                 bg=Style.BACKGROUND, fg=Style.ACCENT_BLUE).pack(pady=(25, 10))
        txt = INFO_TEXTS.get(self.info_key, "Keine Information verfügbar.")
        tk.Label(info_win, text=txt, bg=Style.BACKGROUND, fg=Style.FOREGROUND,
                 font=("Segoe UI", 11), justify=tk.LEFT, wraplength=340).pack(expand=True, fill=tk.BOTH, padx=30)
        tk.Button(info_win, text="SCHLIESSEN", command=info_win.destroy,
                  bg=Style.ACCENT_PURPLE, fg="white", relief=tk.FLAT,
                  font=("Arial", 10, "bold")).pack(pady=25, ipadx=20)


class StreamForgeGUI:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("StreamForge Manager")

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
        self.images = {}
        self.logo_original = None

        self.setup_ui()
        self.setup_callbacks()
        start_hotkey_listener(self.is_server_running)

        # NEU: Startet den Status-Check Loop
        self.update_status_loop()

    def setup_ui(self):
        logo_path = get_path("assets/LOGO.png")
        header = tk.Frame(self.root, bg=Style.BACKGROUND)
        header.pack(fill=tk.X, side=tk.TOP, padx=30, pady=20)

        if os.path.exists(logo_path):
            try:
                pil_icon = Image.open(logo_path).convert("RGBA")
                pil_icon.thumbnail((240, 135), Image.Resampling.LANCZOS)
                self.images['header_icon'] = ImageTk.PhotoImage(pil_icon)
                tk.Label(header, image=self.images['header_icon'], bg=Style.BACKGROUND).pack(side=tk.LEFT, padx=(0, 15))
            except:
                pass

        tk.Label(header, text="STREAMFORGE", font=("Impact", 32),
                 bg=Style.BACKGROUND, fg=Style.FOREGROUND).pack(side=tk.LEFT)

        # --- STATUS CONTROLS (RECHTS) ---
        controls = tk.Frame(header, bg=Style.BACKGROUND)
        controls.pack(side=tk.RIGHT)

        # 1. TIKTOK STATUS
        tk.Label(controls, text="TIKTOK", bg=Style.BACKGROUND, fg="#666666", font=("Arial", 8, "bold")).pack(
            side=tk.LEFT, padx=(0, 5))
        self.tt_canvas = tk.Canvas(controls, width=16, height=16, bg=Style.BACKGROUND, highlightthickness=0)
        self.tt_canvas.pack(side=tk.LEFT)
        self.tt_indicator = self.tt_canvas.create_oval(2, 2, 14, 14, fill="#444444", outline="")

        # Trenner
        tk.Frame(controls, width=1, height=20, bg="#333").pack(side=tk.LEFT, padx=15)

        # 2. SERVER STATUS
        tk.Label(controls, text="SERVER", bg=Style.BACKGROUND, fg="#666666", font=("Arial", 8, "bold")).pack(
            side=tk.LEFT, padx=(0, 5))
        self.status_canvas = tk.Canvas(controls, width=16, height=16, bg=Style.BACKGROUND, highlightthickness=0)
        self.status_canvas.pack(side=tk.LEFT)
        self.status_indicator = self.status_canvas.create_oval(2, 2, 14, 14, fill=Style.DANGER, outline="")

        # 3. USER SETTINGS BUTTON
        tk.Button(controls, text="👤", command=self.open_global_settings,
                  bg=Style.BACKGROUND, fg=Style.ACCENT_BLUE, relief=tk.FLAT,
                  font=("Arial", 20), bd=0, cursor="hand2").pack(side=tk.LEFT, padx=(25, 0))

        # --- FOOTER ---
        footer = tk.Frame(self.root, bg="#111111", height=40)
        footer.pack(fill=tk.X, side=tk.BOTTOM)
        f_content = tk.Frame(footer, bg="#111111")
        f_content.pack(fill=tk.BOTH, padx=20, pady=8)
        tk.Label(f_content, text="v2.1  |  FORGED FOR STREAMERS", font=("Segoe UI", 10, "bold"),
                 bg="#111111", fg="#666666").pack(side=tk.LEFT)
        f_right = tk.Frame(f_content, bg="#111111")
        f_right.pack(side=tk.RIGHT)
        if os.path.exists(get_path("assets/icon.ico")):
            try:
                pil_f = Image.open(get_path("assets/icon.ico")).convert("RGBA")
                pil_f.thumbnail((100, 100), Image.Resampling.LANCZOS)
                self.images['footer_logo'] = ImageTk.PhotoImage(pil_f)
                tk.Label(f_right, image=self.images['footer_logo'], bg="#111111").pack(side=tk.RIGHT, padx=(10, 0))
            except:
                pass
        tk.Label(f_right, text="STREAMFORGE SYSTEM", font=("Segoe UI", 9), bg="#111111", fg="#444444").pack(
            side=tk.RIGHT)

        # --- MAIN AREA ---
        main_frame = tk.Frame(self.root, bg=Style.BACKGROUND)
        main_frame.pack(fill=tk.BOTH, expand=True)
        self.canvas = tk.Canvas(main_frame, bg=Style.BACKGROUND, highlightthickness=0)
        self.scrollbar = tk.Scrollbar(main_frame, orient="vertical", command=self.canvas.yview)
        self.canvas.configure(yscrollcommand=self.scrollbar.set)
        self.scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.canvas.bind_all("<MouseWheel>", self._on_mousewheel)

        # MODULE
        self.cards.append(DashboardCard(
            self.canvas, "LIKES",
            [("Challenge Text", "like_overlay/index.html"), ("Progress Bar", "like_progress_bar/index.html")],
            settings_func=self.open_like_challenge_settings_window,
            test_func=self.test_likes_action, test_label="TEST +100", info_key="LIKES"))

        self.cards.append(DashboardCard(
            self.canvas, "TIMER & SUBATHON",
            [("Subathon Info", "subathon_overlay/index.html"), ("Timer Overlay", "timer_overlay/index.html"),
             ("Gambit Overlay", "gambler_overlay/index.html")],
            settings_func=self.open_subathon_settings_window, info_key="TIMER",
            custom_buttons=[("START", lambda: self.control_timer("start"), Style.SUCCESS),
                            ("PAUSE", lambda: self.control_timer("pause"), Style.ACCENT_BLUE),
                            ("RESET", lambda: self.control_timer("reset"), Style.DANGER),
                            ("GAMBIT", self.test_gambit_action, "#d4af37")]))

        self.cards.append(DashboardCard(
            self.canvas, "KILLER WISHES",
            [("Wishlist Overlay", "killer_wishes/index.html"), ("Place Overlay (!place)", "place_overlay/index.html")],
            reset_func=self.reset_database_action, info_key="WISHES",
            custom_buttons=[("ADD +1", self.test_wish_action, Style.ACCENT_PURPLE),
                            ("CHECK PLACE", self.test_place_action, Style.ACCENT_BLUE)]))

        self.cards.append(DashboardCard(
            self.canvas, "COMMANDS",
            [("Media Overlay", "commands/index.html")],
            settings_func=self.open_commands_settings_window,
            test_func=self.test_command_action, test_label="FIRE SEQUENZ", info_key="COMMANDS"))

        self.canvas.bind("<Configure>", self.on_resize)

    # --- STATUS LOOP ---
    def update_status_loop(self):
        """Prüft jede Sekunde den TikTok Status und aktualisiert die LED."""
        tt_color = "#444444"  # Grau (Initial/Unbekannt)

        if hasattr(like_service_instance, 'api_client') and like_service_instance.api_client:
            if like_service_instance.api_client.is_connected:
                tt_color = Style.SUCCESS  # Grün
            else:
                tt_color = Style.DANGER  # Rot

        self.tt_canvas.itemconfig(self.tt_indicator, fill=tt_color)
        self.root.after(1000, self.update_status_loop)

    # --- RESTLICHE GUI METHODEN (Unverändert) ---
    def on_resize(self, event):
        w = event.width
        card_w, card_h, gap = 280, 220, 25
        cols = max(1, (w - gap) // (card_w + gap))

        for win in self.card_windows: self.canvas.delete(win)
        self.card_windows.clear()

        start_x = (w - (cols * card_w + (cols - 1) * gap)) // 2

        for i, card in enumerate(self.cards):
            r, c = divmod(i, cols)
            x = start_x + c * (card_w + gap)
            y = 30 + r * (card_h + gap)
            self.card_windows.append(self.canvas.create_window(x, y, window=card, anchor="nw"))

        self.canvas.configure(scrollregion=(0, 0, w, 30 + (len(self.cards) // cols + 1) * (card_h + gap) + 50))
        self._update_bg_logo(w, self.canvas.winfo_height())

    def _update_bg_logo(self, view_w, view_h):
        if not self.logo_original: return
        self.canvas.delete("fixed_logo")
        offset_y = self.canvas.canvasy(0)
        if 'bg_logo_cache' not in self.images:
            resized = self.logo_original.copy()
            resized.thumbnail((400, 400), Image.Resampling.LANCZOS)
            self.images['bg_logo_cache'] = ImageTk.PhotoImage(resized)
        img = self.images['bg_logo_cache']
        self.canvas.create_image(view_w - 30, offset_y + view_h - 30, image=img, anchor="se", tags="fixed_logo")
        self.canvas.tag_lower("fixed_logo")

    def _on_mousewheel(self, event):
        self.canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

    def test_gambit_action(self):
        if self.is_server_running[0]:
            requests.post(f"http://{BASE_HOST}:{BASE_PORT}/api/v1/events/gambler")
            show_toast(self.root, "Gambit gestartet!", "#d4af37")
        else:
            show_toast(self.root, "Server offline", Style.DANGER)

    def test_likes_action(self):
        if self.is_server_running[0]: requests.post(
            f"http://{BASE_HOST}:{BASE_PORT}/api/v1/like_challenge/test"); show_toast(self.root, "100 Likes")

    def test_wish_action(self):
        if self.is_server_running[0]: requests.post(f"http://{BASE_HOST}:{BASE_PORT}/api/v1/wishes",
                                                    json={"wunsch": "Test", "user_name": "Tester"}); show_toast(
            self.root, "+1 Wunsch")

    def test_place_action(self):
        if not self.is_server_running[0]: return

        def t():
            try:
                r = requests.get(f"http://{BASE_HOST}:{BASE_PORT}/api/v1/wishes")
                u = "TestUser"
                if not r.json():
                    requests.post(f"http://{BASE_HOST}:{BASE_PORT}/api/v1/wishes",
                                  json={"wunsch": "T", "user_name": u}); time.sleep(0.2)
                else:
                    u = r.json()[0]['user_name']
                requests.post(f"http://{BASE_HOST}:{BASE_PORT}/api/v1/wishes/check_place", json={"user_name": u})
                self.root.after(0, lambda: show_toast(self.root, f"Place Check: {u}"))
            except:
                pass

        threading.Thread(target=t, daemon=True).start()

    def test_command_action(self):
        if self.is_server_running[0]: requests.post(
            f"http://{BASE_HOST}:{BASE_PORT}{COMMANDS_TRIGGER_ENDPOINT}"); show_toast(self.root, "Command Fire")

    def control_timer(self, a):
        if self.is_server_running[0]: requests.post(f"http://{BASE_HOST}:{BASE_PORT}/api/v1/timer/control",
                                                    json={"action": a}); show_toast(self.root, f"Timer {a}")

    def reset_database_action(self):
        if self.is_server_running[0] and messagebox.askyesno("Reset", "Sicher?"): requests.post(
            f"http://{BASE_HOST}:{BASE_PORT}{RESET_WISHES_ENDPOINT}"); show_toast(self.root, "Reset")

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

        threading.Thread(target=r, daemon=True).start()
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
        self.root.destroy();
        sys.exit(0)

    def start(self):
        from database.db_setup import setup_database
        setup_database()
        self.root.after(100, self.start_webserver)
        self.root.mainloop()


class GlobalSettingsWindow(tk.Toplevel):
    def __init__(self, master):
        super().__init__(master)
        self.title("Settings");
        self.geometry("400x250");
        self.configure(bg=Style.BACKGROUND)
        x = master.winfo_x() + 100;
        y = master.winfo_y() + 100;
        self.geometry(f"+{x}+{y}")
        tk.Label(self, text="TikTok Username (ohne @):", bg=Style.BACKGROUND, fg="white",
                 font=("Arial", 12, "bold")).pack(pady=(30, 5))
        self.uv = tk.StringVar();
        try:
            self.uv.set(like_service_instance.settings_manager.load_settings().get("tiktok_unique_id", ""))
        except:
            pass
        tk.Entry(self, textvariable=self.uv, font=("Arial", 14), bg="#333", fg="white", insertbackground="white",
                 relief=tk.FLAT, justify='center').pack(pady=5, padx=40, fill=tk.X, ipady=5)
        tk.Label(self, text="(Speichern startet Verbindung neu)", bg=Style.BACKGROUND, fg="#666",
                 font=("Arial", 8)).pack()
        tk.Button(self, text="VERBINDEN & SPEICHERN", command=self.save, bg=Style.SUCCESS, fg="white", relief=tk.FLAT,
                  font=("Arial", 10, "bold")).pack(pady=25, ipadx=20, ipady=5)

    def save(self):
        v = self.uv.get().strip()
        if v:
            like_service_instance.update_and_restart(v); show_toast(self.master, f"Verbinde zu {v}..."); self.destroy()
        else:
            messagebox.showwarning("Fehler", "Bitte Username eingeben!")