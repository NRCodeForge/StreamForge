import tkinter as tk
from tkinter import ttk, messagebox
import threading
import sys
import ctypes  # Für Windows Dark Titlebar
from datetime import datetime

# Importe
try:
    from config import Style, BASE_HOST, BASE_PORT
    from services.tiktok_live_wrapper import start_tiktok_process, stop_tiktok_process
    from presentation.settings_windows import SubathonSettingsWindow, LikeChallengeSettingsWindow, \
        CommandsSettingsWindow
    from presentation.web_api import start_flask_server
    from services.service_provider import subathon_service_instance
except ImportError as e:
    print(f"Import Fehler: {e}")
    sys.exit(1)


# --- KONSOLE WIDGET (Redirect Stdout) ---
class ConsoleUi:
    def __init__(self, text_widget):
        self.text_widget = text_widget
        self.text_widget.configure(state='disabled')

    def write(self, message):
        def _append():
            self.text_widget.configure(state='normal')
            timestamp = datetime.now().strftime("[%H:%M:%S] ")
            # Einfaches Highlighting basierend auf Keywords
            tag = "normal"
            if "[ERROR]" in message:
                tag = "error"
            elif "[WARNING]" in message:
                tag = "warning"
            elif "[INFO]" in message:
                tag = "info"

            self.text_widget.insert('end', f"{timestamp} {message}", tag)
            self.text_widget.see('end')
            self.text_widget.configure(state='disabled')

        # Thread-Safe GUI Update
        try:
            self.text_widget.after(0, _append)
        except:
            pass

    def flush(self):
        pass


# --- HAUPT ANWENDUNG ---
class StreamForgeGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("StreamForge: Entity's Realm")
        self.root.geometry("1100x750")
        self.root.configure(bg=Style.BG_MAIN)
        self.root.minsize(900, 600)

        # 1. Windows Dark Title Bar Hack (Macht die Leiste oben schwarz)
        try:
            self.root.update()
            DWMWA_USE_IMMERSIVE_DARK_MODE = 20
            set_window_attribute = ctypes.windll.dwmapi.DwmSetWindowAttribute
            get_parent = ctypes.windll.user32.GetParent
            hwnd = get_parent(self.root.winfo_id())
            rendering_policy = DWMWA_USE_IMMERSIVE_DARK_MODE
            value = 2
            value = ctypes.c_int(value)
            set_window_attribute(hwnd, rendering_policy, ctypes.byref(value), ctypes.sizeof(value))
        except:
            pass  # Ignorieren falls kein Windows

        # 2. Styles Initialisieren
        self._init_styles()

        # 3. Layout Aufbau
        self._build_layout()

        # 4. Stdout Umleiten
        sys.stdout = ConsoleUi(self.console_text)
        # sys.stderr = ConsoleUi(self.console_text) # Optional

    def _init_styles(self):
        style = ttk.Style()
        style.theme_use('clam')  # Clam ist gut anpassbar

        # Notebook (Tabs)
        style.configure("TNotebook", background=Style.BG_MAIN, borderwidth=0)
        style.configure("TNotebook.Tab", background=Style.BG_CARD, foreground=Style.TEXT_DIM,
                        padding=[20, 10], font=Style.FONT_HEADER)
        style.map("TNotebook.Tab",
                  background=[("selected", Style.ACCENT_RED)],
                  foreground=[("selected", "white")])

        # Frames
        style.configure("Card.TFrame", background=Style.BG_CARD, relief="flat")
        style.configure("Main.TFrame", background=Style.BG_MAIN)

        # Buttons (Modern Flat)
        style.configure("Action.TButton", background=Style.ACCENT_RED, foreground="white",
                        font=("Segoe UI", 10, "bold"), borderwidth=0, padding=10)
        style.map("Action.TButton", background=[("active", Style.ACCENT_RED_HOVER)])

        style.configure("Secondary.TButton", background=Style.BG_INPUT, foreground="white",
                        font=("Segoe UI", 10), borderwidth=0, padding=10)
        style.map("Secondary.TButton", background=[("active", Style.BORDER)])

        # Labels
        style.configure("TLabel", background=Style.BG_MAIN, foreground=Style.TEXT_MAIN, font=Style.FONT_BODY)
        style.configure("Card.TLabel", background=Style.BG_CARD, foreground=Style.TEXT_MAIN, font=Style.FONT_BODY)
        style.configure("Header.TLabel", background=Style.BG_CARD, foreground="white", font=Style.FONT_TITLE)
        style.configure("Dim.TLabel", background=Style.BG_CARD, foreground=Style.TEXT_DIM, font=("Segoe UI", 9))

    def _build_layout(self):
        # --- HEADER ---
        header = tk.Frame(self.root, bg=Style.BG_MAIN, height=60, pady=10, padx=20)
        header.pack(fill='x')
        tk.Label(header, text="STREAMFORGE", font=("Impact", 28), bg=Style.BG_MAIN, fg=Style.ACCENT_RED).pack(
            side='left')
        tk.Label(header, text=" // SYSTEM READY", font=("Consolas", 12), bg=Style.BG_MAIN, fg=Style.SUCCESS).pack(
            side='left', padx=10, pady=(12, 0))

        # --- TABS ---
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill='both', expand=True, padx=20, pady=(0, 20))

        # Tab 1: General
        self.tab_general = ttk.Frame(self.notebook, style="Main.TFrame")
        self.notebook.add(self.tab_general, text="  GENERAL  ")
        self._build_general_tab()

        # Tab 2: TikTok
        self.tab_tiktok = ttk.Frame(self.notebook, style="Main.TFrame")
        self.notebook.add(self.tab_tiktok, text="  TIKTOK  ")
        self._build_tiktok_tab()

        # Tab 3: Twitch
        self.tab_twitch = ttk.Frame(self.notebook, style="Main.TFrame")
        self.notebook.add(self.tab_twitch, text="  TWITCH  ")
        self._build_twitch_tab()

    # ------------------------------------------------------------------
    # TAB 1: GENERAL (DASHBOARD)
    # ------------------------------------------------------------------
    def _build_general_tab(self):
        self.tab_general.columnconfigure(0, weight=2)  # Konsole breiter
        self.tab_general.columnconfigure(1, weight=1)  # Controls schmaler
        self.tab_general.rowconfigure(0, weight=1)

        # Links: Live Konsole
        console_frame = ttk.Frame(self.tab_general, style="Card.TFrame", padding=2)  # padding als Border
        console_frame.grid(row=0, column=0, sticky="nsew", padx=(0, 10), pady=20)

        # Inner Frame für Background Color
        inner_console = tk.Frame(console_frame, bg="#000")
        inner_console.pack(fill='both', expand=True)

        tk.Label(inner_console, text="SYSTEM LOG", bg="#000", fg=Style.TEXT_DIM, font=Style.FONT_MONO, anchor='w').pack(
            fill='x', padx=5, pady=2)

        self.console_text = tk.Text(inner_console, bg="#000", fg="#ccc", font=("Consolas", 10),
                                    relief="flat", state="disabled", highlightthickness=0)
        self.console_text.pack(fill='both', expand=True, padx=5, pady=5)

        # Tags für Farben in der Konsole
        self.console_text.tag_config("error", foreground=Style.DANGER)
        self.console_text.tag_config("warning", foreground=Style.WARNING)
        self.console_text.tag_config("info", foreground=Style.ACCENT_BLUE)

        # Rechts: Quick Actions & Overlay Status
        control_panel = tk.Frame(self.tab_general, bg=Style.BG_MAIN)
        control_panel.grid(row=0, column=1, sticky="nsew", pady=20)

        # Card: Overlays
        self._create_dashboard_card(control_panel, "OVERLAY CONTROLS", [
            ("⚙️ Subathon & Timer", self.open_subathon_settings),
            ("❤️ Like Challenge", self.open_like_settings),
            ("🎮 Command Overlay", self.open_command_settings)
        ])

        # Card: System Status
        tk.Frame(control_panel, height=20, bg=Style.BG_MAIN).pack()  # Spacer

        status_card = ttk.Frame(control_panel, style="Card.TFrame", padding=20)
        status_card.pack(fill='x')
        ttk.Label(status_card, text="SYSTEM STATUS", style="Header.TLabel").pack(anchor='w', pady=(0, 10))

        self.status_lbl_server = ttk.Label(status_card, text="⚫ API Server: Offline", style="Card.TLabel")
        self.status_lbl_server.pack(anchor='w', pady=2)
        self.status_lbl_db = ttk.Label(status_card, text="🟢 Database: Connected", style="Card.TLabel")
        self.status_lbl_db.pack(anchor='w', pady=2)

        # Main Start Button
        tk.Frame(control_panel, height=20, bg=Style.BG_MAIN).pack()  # Spacer
        self.btn_start_server = ttk.Button(control_panel, text="▶ START ALL SYSTEMS", style="Action.TButton",
                                           command=self.start_system)
        self.btn_start_server.pack(fill='x', ipady=10)

    def _create_dashboard_card(self, parent, title, buttons):
        card = ttk.Frame(parent, style="Card.TFrame", padding=20)
        card.pack(fill='x')
        ttk.Label(card, text=title, style="Header.TLabel").pack(anchor='w', pady=(0, 15))

        for text, cmd in buttons:
            btn = ttk.Button(card, text=text, style="Secondary.TButton", command=cmd)
            btn.pack(fill='x', pady=5)
        return card

    # ------------------------------------------------------------------
    # TAB 2: TIKTOK
    # ------------------------------------------------------------------
    def _build_tiktok_tab(self):
        center = tk.Frame(self.tab_tiktok, bg=Style.BG_MAIN)
        center.pack(expand=True)  # Zentriert im Tab

        card = ttk.Frame(center, style="Card.TFrame", padding=40)
        card.pack(fill='both')

        # Icon / Title
        ttk.Label(card, text="TIKTOK CONNECTION", style="Header.TLabel", font=("Segoe UI", 24, "bold")).pack(
            pady=(0, 10))
        ttk.Label(card, text="Verbinde StreamForge mit deinem TikTok Live Stream", style="Dim.TLabel").pack(
            pady=(0, 30))

        # Input
        ttk.Label(card, text="TikTok Username (@):", style="Card.TLabel").pack(anchor='w')
        self.tiktok_user_var = tk.StringVar(value="dbdstation")
        entry = tk.Entry(card, textvariable=self.tiktok_user_var, bg=Style.BG_INPUT, fg="white",
                         font=("Segoe UI", 12), relief="flat", insertbackground="white")
        entry.pack(fill='x', pady=(5, 20), ipady=8)

        # Buttons
        btn_frm = tk.Frame(card, bg=Style.BG_CARD)
        btn_frm.pack(fill='x')

        self.btn_tk_connect = ttk.Button(btn_frm, text="CONNECT LIVE", style="Action.TButton",
                                         command=self.toggle_tiktok)
        self.btn_tk_connect.pack(side='left', fill='x', expand=True, padx=(0, 5))

        self.btn_tk_stop = ttk.Button(btn_frm, text="DISCONNECT", style="Secondary.TButton", command=self.stop_tiktok)
        self.btn_tk_stop.pack(side='right', fill='x', expand=True, padx=(5, 0))

        # Status
        self.lbl_tiktok_status = tk.Label(card, text="Status: Getrennt", bg=Style.BG_CARD, fg=Style.TEXT_DIM, pady=20)
        self.lbl_tiktok_status.pack()

    # ------------------------------------------------------------------
    # TAB 3: TWITCH
    # ------------------------------------------------------------------
    def _build_twitch_tab(self):
        center = tk.Frame(self.tab_twitch, bg=Style.BG_MAIN)
        center.pack(expand=True)

        card = ttk.Frame(center, style="Card.TFrame", padding=40)
        card.pack(fill='both')

        ttk.Label(card, text="TWITCH INTEGRATION", style="Header.TLabel", foreground=Style.ACCENT_PURPLE,
                  font=("Segoe UI", 24, "bold")).pack(pady=(0, 10))
        ttk.Label(card, text="Verbinde dich mit dem Twitch EventSub", style="Dim.TLabel").pack(pady=(0, 30))

        # Inputs
        ttk.Label(card, text="Channel Name:", style="Card.TLabel").pack(anchor='w')
        entry_chan = tk.Entry(card, bg=Style.BG_INPUT, fg="white", font=("Segoe UI", 12), relief="flat",
                              insertbackground="white")
        entry_chan.pack(fill='x', pady=(5, 20), ipady=8)

        # Connect Button
        ttk.Button(card, text="CONNECT TWITCH", style="Secondary.TButton").pack(fill='x', ipady=5)

        tk.Label(card, text="Funktion folgt in Kürze...", bg=Style.BG_CARD, fg=Style.ACCENT_PURPLE).pack(pady=20)

    # --- LOGIK & COMMANDS ---

    def start_system(self):
        # 1. Start Flask API
        t = threading.Thread(target=start_flask_server, daemon=True)
        t.start()
        self.status_lbl_server.config(text="🟢 API Server: Online", foreground=Style.SUCCESS)
        print("[INFO] System gestartet. API läuft.")

    def toggle_tiktok(self):
        user = self.tiktok_user_var.get()
        if not user:
            messagebox.showwarning("Fehler", "Bitte Username eingeben")
            return

        self.lbl_tiktok_status.config(text="Verbinde...", fg=Style.WARNING)
        self.btn_tk_connect.state(['disabled'])

        # Starte TikTok Service
        threading.Thread(target=self._run_tiktok, args=(user,), daemon=True).start()

    def _run_tiktok(self, user):
        try:
            start_tiktok_process(user)
            self.root.after(0, lambda: self.lbl_tiktok_status.config(text="🟢 Verbunden", fg=Style.SUCCESS))
        except Exception as e:
            self.root.after(0, lambda: self.lbl_tiktok_status.config(text=f"Fehler: {e}", fg=Style.DANGER))
        finally:
            self.root.after(0, lambda: self.btn_tk_connect.state(['!disabled']))

    def stop_tiktok(self):
        stop_tiktok_process()
        self.lbl_tiktok_status.config(text="🔴 Getrennt", fg=Style.DANGER)
        print("[INFO] TikTok Verbindung getrennt.")

    # Window Openers
    def open_subathon_settings(self):
        SubathonSettingsWindow(self.root)

    def open_like_settings(self):
        LikeChallengeSettingsWindow(self.root)

    def open_command_settings(self):
        CommandsSettingsWindow(self.root)


if __name__ == "__main__":
    root = tk.Tk()
    app = StreamForgeGUI(root)
    root.mainloop()