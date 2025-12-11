import threading
import time
import tkinter as tk
from tkinter import messagebox, font, ttk
import requests
import sys
import os
import webbrowser
from PIL import Image, ImageTk

# Importiere Services und Config
# WICHTIG: CurrencySettingsWindow muss hier importiert werden
from presentation.settings_windows import (
    SubathonSettingsWindow,
    LikeChallengeSettingsWindow,
    CommandsSettingsWindow,
    TimerGambitSettingsWindow,
    CurrencySettingsWindow
)
from services.service_provider import like_service_instance, twitch_service_instance

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
    "SUBATHON": (
        "SUBATHON TRIGGER\n\n"
        "Hier definieren Sie die Trigger für TikTok:\n"
        "Coins, Likes, Follows -> Zeit.\n"
        "Einstellungen: Zahnrad klicken."
    ),
    "TIMER": (
        "TIMER & GAMBIT\n\n"
        "Timer: Startzeit & Event-Dauer konfigurieren.\n"
        "Gambit: Das Glücksrad konfigurieren.\n"
        "Einstellungen: Zahnrad klicken."
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
    ),
    "CURRENCY": (
        "TWITCH WÄHRUNG\n\n"
        "Verwaltet Punkte für Chat-Aktivität, Bits und Subs.\n"
        "Commands: !score (Stand), !send (Überweisen).\n"
        "Einstellungen: Zahnrad klicken."
    )
}


class DashboardCard(tk.Frame):
    """
    Einheitliches Modul für das Grid-Layout.
    """

    def __init__(self, parent, title, items, settings_func=None, test_func=None, reset_func=None, info_key=None,
                 test_label="TEST", custom_buttons=None):
        card_bg = "#1a1a1a"
        # highlightbackground für den Rahmen
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

            if path:  # Nur anzeigen wenn Pfad vorhanden
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

        # Styles für Notebook (Tabs)
        self.setup_styles()

        icon_path = get_path("assets/icon.ico")
        if os.path.exists(icon_path):
            try:
                self.root.iconbitmap(icon_path)
            except:
                pass

        self.is_server_running = [False]
        # Listen für Karten-Management pro Tab
        self.cards_general = []
        self.windows_general = []
        self.cards_tiktok = []
        self.windows_tiktok = []

        self.images = {}

        self.setup_ui()
        self.setup_callbacks()
        start_hotkey_listener(self.is_server_running)

        # Startet den Status-Check Loop
        self.update_status_loop()

    def setup_styles(self):
        style = ttk.Style()
        style.theme_use('clam')

        # Notebook (Tab-Container) Style
        style.configure("TNotebook", background=Style.BACKGROUND, borderwidth=0)
        style.configure("TNotebook.Tab",
                        background="#222222",
                        foreground="#888888",
                        padding=[15, 8],
                        font=("Segoe UI", 10, "bold"),
                        borderwidth=0)
        style.map("TNotebook.Tab",
                  background=[("selected", Style.ACCENT_PURPLE), ("active", "#333333")],
                  foreground=[("selected", "white"), ("active", "white")])

    def setup_ui(self):
        # --- HEADER ---
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

        tk.Frame(controls, width=1, height=20, bg="#333").pack(side=tk.LEFT, padx=10)

        # 2. TWITCH STATUS (NEU)
        tk.Label(controls, text="TWITCH", bg=Style.BACKGROUND, fg="#666666", font=("Arial", 8, "bold")).pack(
            side=tk.LEFT, padx=(0, 5))
        self.tw_canvas = tk.Canvas(controls, width=16, height=16, bg=Style.BACKGROUND, highlightthickness=0)
        self.tw_canvas.pack(side=tk.LEFT)
        self.tw_indicator = self.tw_canvas.create_oval(2, 2, 14, 14, fill="#444444", outline="")

        tk.Frame(controls, width=1, height=20, bg="#333").pack(side=tk.LEFT, padx=10)

        # 3. SERVER STATUS
        tk.Label(controls, text="SERVER", bg=Style.BACKGROUND, fg="#666666", font=("Arial", 8, "bold")).pack(
            side=tk.LEFT, padx=(0, 5))
        self.status_canvas = tk.Canvas(controls, width=16, height=16, bg=Style.BACKGROUND, highlightthickness=0)
        self.status_canvas.pack(side=tk.LEFT)
        self.status_indicator = self.status_canvas.create_oval(2, 2, 14, 14, fill=Style.DANGER, outline="")

        # 4. USER SETTINGS BUTTON
        tk.Button(controls, text="👤", command=self.open_global_settings,
                  bg=Style.BACKGROUND, fg=Style.ACCENT_BLUE, relief=tk.FLAT,
                  font=("Arial", 20), bd=0, cursor="hand2").pack(side=tk.LEFT, padx=(25, 0))

        # --- TABS (NOTEBOOK) ---
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=20, pady=(0, 10))

        self.tab_general = tk.Frame(self.notebook, bg=Style.BACKGROUND)
        self.tab_tiktok = tk.Frame(self.notebook, bg=Style.BACKGROUND)
        self.tab_twitch = tk.Frame(self.notebook, bg=Style.BACKGROUND)

        self.notebook.add(self.tab_general, text="GENERAL")
        self.notebook.add(self.tab_tiktok, text="TIKTOK")
        self.notebook.add(self.tab_twitch, text="TWITCH")

        # --- FOOTER ---
        footer = tk.Frame(self.root, bg="#111111", height=40)
        footer.pack(fill=tk.X, side=tk.BOTTOM)
        f_content = tk.Frame(footer, bg="#111111")
        f_content.pack(fill=tk.BOTH, padx=20, pady=8)
        tk.Label(f_content, text="v2.3  |  FORGED FOR STREAMERS", font=("Segoe UI", 10, "bold"),
                 bg="#111111", fg="#666666").pack(side=tk.LEFT)

        # --- SETUP CONTENT FOR TABS ---
        self.canvas_general = self.create_scrollable_tab(self.tab_general, "general")
        self.canvas_tiktok = self.create_scrollable_tab(self.tab_tiktok, "tiktok")
        self.canvas_twitch = self.create_scrollable_tab(self.tab_twitch, "twitch")  # Scrollbarer Twitch Tab

        # --- POPULATE TIKTOK TAB ---
        self.cards_tiktok.append(DashboardCard(
            self.canvas_tiktok, "LIKES",
            [("Challenge Text", "like_overlay/index.html"), ("Progress Bar", "like_progress_bar/index.html")],
            settings_func=self.open_like_challenge_settings_window,
            test_func=self.test_likes_action, test_label="TEST +100", info_key="LIKES"))

        self.cards_tiktok.append(DashboardCard(
            self.canvas_tiktok, "SUBATHON TRIGGER",
            [("Subathon Info", "subathon_overlay/index.html")],
            settings_func=self.open_subathon_settings_window,
            info_key="SUBATHON"))

        # --- POPULATE TWITCH TAB ---
        # Währungssystem
        DashboardCard(
            self.canvas_twitch, "TWITCH WÄHRUNG",
            [("Commands: !score, !send", "")],  # Kein Web-Link nötig vorerst
            settings_func=self.open_currency_settings,
            info_key="CURRENCY"
        ).pack(padx=25, pady=30, anchor="nw")  # Direkt packen da nur 1 Item bisher

        # --- POPULATE GENERAL TAB ---
        self.cards_general.append(DashboardCard(
            self.canvas_general, "TIMER & GAMBIT",
            [("Timer Overlay", "timer_overlay/index.html"),
             ("Gambit Overlay", "gambler_overlay/index.html")],
            settings_func=self.open_timer_gambit_settings,
            info_key="TIMER",
            custom_buttons=[("START", lambda: self.control_timer("start"), Style.SUCCESS),
                            ("PAUSE", lambda: self.control_timer("pause"), Style.ACCENT_BLUE),
                            ("RESET", lambda: self.control_timer("reset"), Style.DANGER),
                            ("GAMBIT", self.test_gambit_action, "#d4af37")]))

        self.cards_general.append(DashboardCard(
            self.canvas_general, "KILLER WISHES",
            [("Wishlist Overlay", "killer_wishes/index.html"), ("Place Overlay (!place)", "place_overlay/index.html")],
            reset_func=self.reset_database_action, info_key="WISHES",
            custom_buttons=[("ADD +1", self.test_wish_action, Style.ACCENT_PURPLE),
                            ("CHECK PLACE", self.test_place_action, Style.ACCENT_BLUE)]))

        self.cards_general.append(DashboardCard(
            self.canvas_general, "COMMANDS",
            [("Media Overlay", "commands/index.html")],
            settings_func=self.open_commands_settings_window,
            test_func=self.test_command_action, test_label="FIRE SEQUENZ", info_key="COMMANDS"))

        self.tab_general.bind("<Configure>", lambda e: self.on_resize(e, self.canvas_general, self.cards_general,
                                                                      self.windows_general))
        self.tab_tiktok.bind("<Configure>",
                             lambda e: self.on_resize(e, self.canvas_tiktok, self.cards_tiktok, self.windows_tiktok))

    def create_scrollable_tab(self, parent_frame, tag):
        canvas = tk.Canvas(parent_frame, bg=Style.BACKGROUND, highlightthickness=0)
        scrollbar = tk.Scrollbar(parent_frame, orient="vertical", command=canvas.yview)
        canvas.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        canvas.bind("<Enter>", lambda _: canvas.bind_all("<MouseWheel>", lambda e: self._on_mousewheel(e, canvas)))
        canvas.bind("<Leave>", lambda _: canvas.unbind_all("<MouseWheel>"))
        return canvas

    # --- STATUS LOOP (NEU MIT TWITCH) ---
    def update_status_loop(self):
        # 1. TikTok Status
        tt_color = "#444444"
        if hasattr(like_service_instance, 'api_client') and like_service_instance.api_client:
            if like_service_instance.api_client.is_connected:
                tt_color = Style.SUCCESS
            else:
                tt_color = Style.DANGER
        self.tt_canvas.itemconfig(self.tt_indicator, fill=tt_color)

        # 2. Twitch Status
        tw_color = "#444444"
        try:
            ts = twitch_service_instance.get_status()
            if ts.get("connected"):
                tw_color = "#9146FF"  # Twitch Purple
            else:
                tw_color = "#444444"
        except:
            pass
        self.tw_canvas.itemconfig(self.tw_indicator, fill=tw_color)

        self.root.after(1000, self.update_status_loop)

    def on_resize(self, event, canvas, cards, windows_list):
        w = event.width
        if w < 10: return
        card_w, card_h, gap = 280, 220, 25
        cols = max(1, (w - gap) // (card_w + gap))
        for win in windows_list: canvas.delete(win)
        windows_list.clear()
        start_x = (w - (cols * card_w + (cols - 1) * gap)) // 2
        for i, card in enumerate(cards):
            r, c = divmod(i, cols)
            x = start_x + c * (card_w + gap)
            y = 30 + r * (card_h + gap)
            windows_list.append(canvas.create_window(x, y, window=card, anchor="nw"))
        canvas.configure(scrollregion=(0, 0, w, 30 + (len(cards) // cols + 1) * (card_h + gap) + 50))

    def _on_mousewheel(self, event, canvas):
        canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

    # --- ACTIONS ---
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
                                  json={"wunsch": "T", "user_name": u});
                    time.sleep(0.2)
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

    def open_timer_gambit_settings(self):
        TimerGambitSettingsWindow(self.root)

    def open_like_challenge_settings_window(self):
        LikeChallengeSettingsWindow(self.root)

    def open_commands_settings_window(self):
        CommandsSettingsWindow(self.root)

    # NEU: Währungseinstellungen
    def open_currency_settings(self):
        CurrencySettingsWindow(self.root)

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


# --- GLOBAL SETTINGS WINDOW (MIT STATUS UPDATE FIX) ---
class GlobalSettingsWindow(tk.Toplevel):
    def __init__(self, master):
        super().__init__(master)
        self.title("Global Settings & Accounts")
        self.geometry("500x650")
        self.configure(bg=Style.BACKGROUND)

        self.update_idletasks()
        w, h = self.winfo_width(), self.winfo_height()
        x = master.winfo_x() + (master.winfo_width() // 2) - (w // 2)
        y = master.winfo_y() + (master.winfo_height() // 2) - (h // 2)
        self.geometry(f'+{x}+{y}')

        self.settings_mgr = like_service_instance.settings_manager
        self.current_settings = self.settings_mgr.load_settings()

        notebook = ttk.Notebook(self)
        notebook.pack(fill='both', expand=True, padx=10, pady=10)

        self.tab_tiktok = tk.Frame(notebook, bg=Style.BACKGROUND)
        self.tab_twitch = tk.Frame(notebook, bg=Style.BACKGROUND)

        notebook.add(self.tab_tiktok, text="TikTok Live")
        notebook.add(self.tab_twitch, text="Twitch Bot")

        self._build_tiktok_tab()
        self._build_twitch_tab()

    def _build_tiktok_tab(self):
        f = self.tab_tiktok
        tk.Label(f, text="TikTok Konfiguration", bg=Style.BACKGROUND, fg=Style.ACCENT_BLUE,
                 font=("Segoe UI", 12, "bold")).pack(pady=20)
        tk.Label(f, text="Username:", bg=Style.BACKGROUND, fg="white").pack(anchor='w', padx=20)
        self.tt_user = tk.Entry(f, font=("Segoe UI", 10), bg="#333", fg="white", relief=tk.FLAT)
        self.tt_user.insert(0, self.current_settings.get("tiktok_unique_id", ""))
        self.tt_user.pack(fill='x', padx=20, pady=5)
        tk.Button(f, text="💾 TikTok Speichern", command=self.save_tiktok, bg=Style.SUCCESS, fg="white",
                  relief=tk.FLAT).pack(pady=20, fill='x', padx=20)

    def _build_twitch_tab(self):
        f = self.tab_twitch
        tk.Label(f, text="Twitch Authentifizierung", bg=Style.BACKGROUND, fg="#9146FF",
                 font=("Segoe UI", 12, "bold")).pack(pady=20)

        info = ("1. Erstelle eine App auf dev.twitch.tv (Name: StreamForge).\n"
                "2. Setze Redirect URI auf: http://localhost:5000/auth/twitch/callback\n"
                "3. Kopiere die Client ID hier rein.")
        tk.Label(f, text=info, bg=Style.BACKGROUND, fg="#aaa", justify="left").pack(pady=(0, 15))

        tk.Label(f, text="Client ID:", bg=Style.BACKGROUND, fg="white").pack(anchor='w', padx=20)
        self.client_id_var = tk.StringVar(value=self.current_settings.get("twitch_client_id", ""))
        tk.Entry(f, textvariable=self.client_id_var, bg="#333", fg="white", relief=tk.FLAT).pack(fill='x', padx=20,
                                                                                                 pady=5)

        tk.Button(f, text="🔑 Login mit Twitch", command=self.do_twitch_login,
                  bg="#9146FF", fg="white", font=("Segoe UI", 10, "bold"), relief=tk.FLAT).pack(pady=15, fill='x',
                                                                                                padx=20)

        # STATUS LABEL (LIVE)
        self.status_frame = tk.Frame(f, bg=Style.BACKGROUND, highlightbackground="#333", highlightthickness=1)
        self.status_frame.pack(fill='x', padx=20, pady=10)

        self.status_lbl = tk.Label(self.status_frame, text="Lade Status...", bg=Style.BACKGROUND, fg="#aaa",
                                   font=("Segoe UI", 10))
        self.status_lbl.pack(pady=10)

        # Startet den Loop, der alle 1s den Status prüft
        self.update_status_loop()

    def update_status_loop(self):
        if not self.winfo_exists(): return

        try:
            status = twitch_service_instance.get_status()
            if status.get("connected"):
                self.status_lbl.config(text=f"✅ VERBUNDEN als: {status.get('username')}", fg=Style.SUCCESS)
            else:
                self.status_lbl.config(text="❌ NICHT VERBUNDEN", fg=Style.DANGER)
        except Exception as e:
            # Fehler abfangen, aber GUI nicht crashen lassen
            self.status_lbl.config(text="⚠️ Service lädt...", fg="#ffaa00")

        self.after(1000, self.update_status_loop)

    def save_tiktok(self):
        self.current_settings["tiktok_unique_id"] = self.tt_user.get()
        self.settings_mgr.save_settings(self.current_settings)
        like_service_instance.update_and_restart(self.tt_user.get())
        show_toast(self.master, "TikTok gespeichert!")

    def do_twitch_login(self):
        cid = self.client_id_var.get().strip()
        if not cid:
            messagebox.showerror("Fehler", "Bitte Client ID eingeben!")
            return
        self.current_settings["twitch_client_id"] = cid
        self.settings_mgr.save_settings(self.current_settings)

        redirect = "http://localhost:5000/auth/twitch/callback"
        scope = "chat:read+chat:edit"
        url = (f"https://id.twitch.tv/oauth2/authorize?response_type=token"
               f"&client_id={cid}&redirect_uri={redirect}&scope={scope}")

        webbrowser.open(url)
        show_toast(self.master, "Browser geöffnet! Bitte einloggen.")