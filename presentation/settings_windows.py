import tkinter as tk
from tkinter import ttk, messagebox, colorchooser
import sys

try:
    from services.service_provider import subathon_service_instance, like_service_instance, command_service_instance
    from config import Style
    from presentation.ui_elements import show_toast
except ImportError:
    # Fallback damit IDE nicht meckert
    from config import Style


    def show_toast(m, t):
        print(t)


# --- BASIS KLASSE (DBD Style) ---
class BaseSettingsWindow(tk.Toplevel):
    def __init__(self, master, title, width=1000, height=800):
        super().__init__(master)
        self.title(title)
        self.geometry(f"{width}x{height}")
        self.configure(bg=Style.BG_MAIN)
        self.minsize(900, 600)

        # Zentrieren
        self.update_idletasks()
        w, h = self.winfo_width(), self.winfo_height()
        x = master.winfo_x() + (master.winfo_width() // 2) - (w // 2)
        y = master.winfo_y() + (master.winfo_height() // 2) - (h // 2)
        self.geometry(f'+{x}+{y}')

        # Styles
        self.entry_conf = {
            "bg": Style.BG_INPUT, "fg": "white", "relief": "flat",
            "insertbackground": "white", "font": ("Segoe UI", 10)
        }

    def _create_card(self, parent, title):
        card = tk.LabelFrame(parent, text=f" {title} ", bg=Style.BG_CARD, fg=Style.TEXT_MAIN,
                             font=Style.FONT_HEADER, relief="flat", padx=20, pady=20)
        return card


# --- SUBATHON SETTINGS ---
class SubathonSettingsWindow(BaseSettingsWindow):
    def __init__(self, master):
        super().__init__(master, "Subathon Configuration", 1100, 800)
        self.service = subathon_service_instance
        self.settings = self.service.get_current_settings()

        self.gambit_map = {
            "Zeit hinzufügen (+)": "time_add", "Zeit abziehen (-)": "time_sub",
            "✖️ Multiplikator": "time_multi_add", "➗ Teiler": "time_multi_sub",
            "❄️ Freezer": "event_freezer", "⏩ Warp": "event_warp",
            "🙈 Blind": "event_blind", "🔥 Hype": "event_hype", "💬 Text": "text"
        }
        self.gambit_map_rev = {v: k for k, v in self.gambit_map.items()}

        # Styles Setup
        style = ttk.Style()
        style.configure("TNotebook", background=Style.BG_MAIN, borderwidth=0)
        style.configure("TNotebook.Tab", background=Style.BG_CARD, foreground=Style.TEXT_DIM, padding=[20, 10],
                        font=Style.FONT_HEADER)
        style.map("TNotebook.Tab", background=[("selected", Style.ACCENT_RED)], foreground=[("selected", "white")])

        # Header
        header = tk.Frame(self, bg=Style.BG_MAIN, pady=20, padx=20)
        header.pack(fill='x')
        tk.Label(header, text="SUBATHON ENGINE", font=("Impact", 24), bg=Style.BG_MAIN, fg="white").pack(side='left')
        tk.Label(header, text="/// CONFIGURATION", font=("Consolas", 14), bg=Style.BG_MAIN, fg=Style.ACCENT_RED).pack(
            side='left', padx=10)

        # Tabs
        self.notebook = ttk.Notebook(self)
        self.notebook.pack(fill='both', expand=True, padx=20, pady=(0, 20))

        # Tabs erstellen
        self.tab_gen = tk.Frame(self.notebook, bg=Style.BG_MAIN);
        self.notebook.add(self.tab_gen, text="GENERAL")
        self.tab_gam = tk.Frame(self.notebook, bg=Style.BG_MAIN);
        self.notebook.add(self.tab_gam, text="GAMBIT")
        self.tab_tik = tk.Frame(self.notebook, bg=Style.BG_MAIN);
        self.notebook.add(self.tab_tik, text="TIKTOK")
        self.tab_twi = tk.Frame(self.notebook, bg=Style.BG_MAIN);
        self.notebook.add(self.tab_twi, text="TWITCH")

        self._build_gen();
        self._build_gam();
        self._build_tik();
        self._build_twi()

        # Footer
        footer = tk.Frame(self, bg=Style.BG_MAIN, padx=20, pady=20)
        footer.pack(fill='x')
        tk.Button(footer, text="SAVE CONFIGURATION", command=self.save, bg=Style.SUCCESS, fg="white",
                  font=("Segoe UI", 11, "bold"), relief="flat", pady=10, cursor="hand2").pack(fill='x')

    def _build_gen(self):
        container = tk.Frame(self.tab_gen, bg=Style.BG_MAIN)
        container.pack(fill='both', expand=True, padx=20, pady=20)
        container.columnconfigure(0, weight=1);
        container.columnconfigure(1, weight=1)

        # Timer Card
        c1 = self._create_card(container, "TIMER SETTINGS")
        c1.grid(row=0, column=0, sticky="nsew", padx=(0, 10))
        tk.Label(c1, text="Startzeit (Sekunden):", bg=Style.BG_CARD, fg=Style.TEXT_DIM).pack(anchor='w', pady=(10, 5))
        self.start_time = tk.Entry(c1, **self.entry_conf)
        self.start_time.insert(0, self.settings.get("start_time_seconds", 3600))
        self.start_time.pack(fill='x', ipady=5)

        # Duration Card
        c2 = self._create_card(container, "EVENT DURATIONS")
        c2.grid(row=0, column=1, sticky="nsew", padx=(10, 0))
        self.durations = {}
        for i, (k, l) in enumerate(
                [("freezer", "❄️ Freezer"), ("warp", "⏩ Warp"), ("blind", "🙈 Blind"), ("hype", "🔥 Hype")]):
            f = tk.Frame(c2, bg=Style.BG_CARD);
            f.pack(fill='x', pady=5)
            tk.Label(f, text=l, width=15, anchor='w', bg=Style.BG_CARD, fg="white", font=("Segoe UI", 10, "bold")).pack(
                side='left')
            e = tk.Entry(f, **self.entry_conf, justify='center', width=10)
            e.insert(0, self.settings.get(f"duration_{k}", 60))
            e.pack(side='left', padx=10, ipady=3)
            self.durations[k] = e

    def _build_gam(self):
        paned = tk.PanedWindow(self.tab_gam, orient='horizontal', bg=Style.BG_MAIN, sashwidth=4)
        paned.pack(fill='both', expand=True, padx=20, pady=20)

        # Liste
        c_list = self._create_card(paned, "OUTCOMES")
        paned.add(c_list, minsize=400)

        # Treeview Style
        style = ttk.Style()
        style.configure("Treeview", background=Style.BG_INPUT, foreground="white", fieldbackground=Style.BG_INPUT,
                        rowheight=25, borderwidth=0)
        style.configure("Treeview.Heading", background=Style.BG_CARD, foreground="white", font=("Segoe UI", 10, "bold"))
        style.map("Treeview", background=[('selected', Style.ACCENT_RED)])

        self.tree = ttk.Treeview(c_list, columns=("t", "y", "v"), show='headings')
        self.tree.heading("t", text="Text");
        self.tree.heading("y", text="Effect");
        self.tree.heading("v", text="Value")
        self.tree.column("t", width=150);
        self.tree.column("y", width=100);
        self.tree.column("v", width=50)
        self.tree.pack(fill='both', expand=True, pady=10)
        self.tree.bind("<<TreeviewSelect>>", self._on_sel)

        # Editor
        c_edit = self._create_card(paned, "EDITOR")
        paned.add(c_edit, minsize=350)

        tk.Label(c_edit, text="Text:", bg=Style.BG_CARD, fg=Style.TEXT_DIM).pack(anchor='w')
        self.g_txt = tk.Entry(c_edit, **self.entry_conf);
        self.g_txt.pack(fill='x', pady=(0, 10), ipady=5)

        tk.Label(c_edit, text="Type:", bg=Style.BG_CARD, fg=Style.TEXT_DIM).pack(anchor='w')
        self.g_type = ttk.Combobox(c_edit, values=list(self.gambit_map.keys()), state="readonly")
        self.g_type.pack(fill='x', pady=(0, 10), ipady=5)

        tk.Label(c_edit, text="Value:", bg=Style.BG_CARD, fg=Style.TEXT_DIM).pack(anchor='w')
        self.g_val = tk.Entry(c_edit, **self.entry_conf);
        self.g_val.pack(fill='x', pady=(0, 10), ipady=5)

        tk.Label(c_edit, text="Color:", bg=Style.BG_CARD, fg=Style.TEXT_DIM).pack(anchor='w')
        self.g_col_btn = tk.Button(c_edit, bg="white", command=self._col, relief="flat");
        self.g_col_btn.pack(anchor='w', ipadx=20, pady=(0, 20))
        self.curr_col = "#FFFFFF"

        tk.Button(c_edit, text="ADD / UPDATE", command=self._add, bg=Style.ACCENT_RED, fg="white", relief="flat",
                  pady=8).pack(fill='x', pady=2)
        tk.Button(c_edit, text="DELETE", command=self._del, bg=Style.BG_INPUT, fg="white", relief="flat", pady=8).pack(
            fill='x', pady=2)

        self._load_gam()

    def _build_tik(self):
        self._build_list(self.tab_tik, "TIKTOK TRIGGERS", "tiktok")

    def _build_twi(self):
        self._build_list(self.tab_twi, "TWITCH TRIGGERS", "twitch")

    def _build_list(self, parent, title, platform):
        c = self._create_card(parent, title)
        c.pack(fill='both', expand=True, padx=20, pady=20)

        if platform == "tiktok":
            self.tk_w = {}
            target = self.tk_w
            rows = [("coins", "💰 Coin"), ("like", "❤️ Like"), ("share", "↪️ Share"), ("follow", "➕ Follow"),
                    ("subscribe", "⭐ Sub")]
        else:
            self.tw_w = {}
            target = self.tw_w
            rows = [("twitch_sub", "⭐ Sub"), ("twitch_prime", "👑 Prime"), ("twitch_bits", "💎 Bits"),
                    ("twitch_follow", "💜 Follow")]

        for k, n in rows:
            r = tk.Frame(c, bg=Style.BG_CARD, pady=5);
            r.pack(fill='x')
            tk.Label(r, text=n, width=20, anchor='w', bg=Style.BG_CARD, fg="white", font=("Segoe UI", 11)).pack(
                side='left')

            d = self.settings.get(k, {"value": "0", "active": False})
            e = tk.Entry(r, **self.entry_conf, justify='center', width=10)
            e.insert(0, d.get("value", 0));
            e.pack(side='left', padx=10, ipady=3)

            v = tk.BooleanVar(value=d.get("active", False))
            tk.Checkbutton(r, text="ACTIVE", variable=v, bg=Style.BG_CARD, fg="white", selectcolor=Style.BG_MAIN,
                           activebackground=Style.BG_CARD, activeforeground="white").pack(side='left')
            target[k] = {"e": e, "v": v}

    # Logic Helper
    def _load_gam(self):
        for i in self.tree.get_children(): self.tree.delete(i)
        for o in self.settings.get("gambit_outcomes", []):
            self.tree.insert('', 'end', values=(o.get('text'), self.gambit_map_rev.get(o.get('type'), o.get('type')),
                                                o.get('value')))

    def _on_sel(self, e):
        s = self.tree.selection()
        if not s: return
        v = self.tree.item(s[0])['values']
        self.g_txt.delete(0, 'end');
        self.g_txt.insert(0, v[0])
        self.g_type.set(v[1])
        self.g_val.delete(0, 'end');
        self.g_val.insert(0, v[2])

    def _col(self):
        c = colorchooser.askcolor(color=self.curr_col)[1]
        if c: self.curr_col = c; self.g_col_btn.config(bg=c)

    def _add(self):
        try:
            new = {"text": self.g_txt.get(), "type": self.gambit_map.get(self.g_type.get()),
                   "value": float(self.g_val.get()), "color": self.curr_col}
            if "gambit_outcomes" not in self.settings: self.settings["gambit_outcomes"] = []
            self.settings["gambit_outcomes"].append(new)
            self._load_gam()
        except:
            messagebox.showerror("Err", "Input Error")

    def _del(self):
        s = self.tree.selection()
        if s: del self.settings["gambit_outcomes"][self.tree.index(s[0])]; self._load_gam()

    def save(self):
        try:
            self.settings["start_time_seconds"] = self.start_time.get()
            for k, e in self.durations.items(): self.settings[f"duration_{k}"] = e.get()
            if hasattr(self, 'tk_w'):
                for k, w in self.tk_w.items(): self.settings[k] = {"value": w["e"].get(), "active": w["v"].get()}
            if hasattr(self, 'tw_w'):
                for k, w in self.tw_w.items(): self.settings[k] = {"value": w["e"].get(), "active": w["v"].get()}
            self.service.update_settings(self.settings)
            show_toast(self.master, "Settings Saved")
            self.destroy()
        except Exception as e:
            messagebox.showerror("Error", str(e))


# --- COMMANDS & LIKE WINDOWS (Kurzfassung im neuen Style) ---
class LikeChallengeSettingsWindow(BaseSettingsWindow):
    def __init__(self, master):
        super().__init__(master, "Like Challenge", 600, 500)
        self.service = like_service_instance
        c = self._create_card(self, "CONFIGURATION")
        c.pack(fill='both', expand=True, padx=20, pady=20)

        try:
            cs = self.service.settings_manager.load_settings()
        except:
            cs = {}

        self.ents = {}
        for i, (l, k) in enumerate([("Format:", "displayTextFormat"), ("Formula:", "recurringGoalExpression")]):
            tk.Label(c, text=l, bg=Style.BG_CARD, fg="white").pack(anchor='w', pady=(10, 0))
            e = tk.Entry(c, **self.entry_conf);
            e.insert(0, cs.get(k, ""));
            e.pack(fill='x', ipady=5)
            self.ents[k] = e

        tk.Label(c, text="Initial Goals (comma sep):", bg=Style.BG_CARD, fg="white").pack(anchor='w', pady=(10, 0))
        self.goals = tk.Entry(c, **self.entry_conf);
        self.goals.insert(0, ",".join(map(str, cs.get("initialGoals", []))));
        self.goals.pack(fill='x', ipady=5)

        tk.Button(c, text="SAVE", command=self.save, bg=Style.ACCENT_RED, fg="white", relief="flat", pady=10).pack(
            fill='x', pady=20)

    def save(self):
        s = self.service.settings_manager.load_settings()
        s.update({k: self.ents[k].get() for k in self.ents})
        val = self.goals.get().strip()
        s["initialGoals"] = sorted([int(x.strip()) for x in val.split(',') if x.strip()]) if val else []
        self.service.settings_manager.save_settings(s)
        self.destroy()


class CommandsSettingsWindow(BaseSettingsWindow):
    def __init__(self, master):
        super().__init__(master, "Command Overlay", 800, 600)
        self.service = command_service_instance
        c = self._create_card(self, "COMMANDS LIST")
        c.pack(fill='both', expand=True, padx=20, pady=20)

        self.tree = ttk.Treeview(c, columns=("t", "c"), show='headings')
        self.tree.heading("t", text="Trigger");
        self.tree.heading("c", text="Cost")
        self.tree.pack(fill='both', expand=True)

        f = tk.Frame(c, bg=Style.BG_CARD);
        f.pack(fill='x', pady=10)
        self.t = tk.Entry(f, **self.entry_conf);
        self.t.pack(side='left', fill='x', expand=True, padx=5, ipady=5)
        self.v = tk.Entry(f, **self.entry_conf, width=10);
        self.v.pack(side='left', padx=5, ipady=5)
        tk.Button(f, text="+", command=self.add, bg=Style.ACCENT_RED, fg="white", relief="flat").pack(side='left')

        self.load()

    def load(self):
        for i in self.tree.get_children(): self.tree.delete(i)
        for c in self.service.get_all_commands(): self.tree.insert('', 'end', values=(c.get('text'), c.get('costs')))

    def add(self):
        try:
            self.service.add_command(self.t.get(), self.v.get(), False); self.load()
        except:
            pass