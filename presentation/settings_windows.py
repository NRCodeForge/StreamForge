import tkinter as tk
from tkinter import messagebox, font, ttk, colorchooser
import sys
import uuid

# Falls imports lokal nicht gehen, Dummy-Klassen nutzen.
from services.service_provider import like_service_instance, subathon_service_instance, command_service_instance
from config import Style
from presentation.ui_elements import show_toast


# --- BASIS KLASSE ---
class BaseSettingsWindow(tk.Toplevel):
    def __init__(self, master, title, width=600, height=500):
        super().__init__(master)
        self.title(title)
        self.geometry(f"{width}x{height}")
        self.configure(bg=Style.BACKGROUND)

        # Zentrieren
        self.update_idletasks()
        w, h = self.winfo_width(), self.winfo_height()
        x = master.winfo_x() + (master.winfo_width() // 2) - (w // 2)
        y = master.winfo_y() + (master.winfo_height() // 2) - (h // 2)
        self.geometry(f'+{x}+{y}')

        # Styles
        self.label_style = {"bg": Style.BACKGROUND, "fg": "#ecf0f1"}
        self.label_header = {"bg": Style.BACKGROUND, "fg": Style.ACCENT_BLUE, "font": ("Segoe UI", 11, "bold")}

        self.entry_style = {"bg": "#333", "fg": "white", "relief": "flat", "insertbackground": "white"}
        self.btn_style = {"bg": Style.ACCENT_PURPLE, "fg": "white", "relief": "flat", "cursor": "hand2",
                          "font": ("Segoe UI", 9, "bold")}


# --- 1. TIKTOK / SUBATHON SETTINGS (Nur Trigger) ---
class SubathonSettingsWindow(BaseSettingsWindow):
    def __init__(self, master):
        super().__init__(master, "TikTok & Subathon Trigger", 600, 500)
        self.service = subathon_service_instance
        # Lade aktuelle Einstellungen
        self.settings = self.service.get_current_settings()

        tk.Label(self, text="TikTok Aktionen & Trigger", font=("Segoe UI", 14, "bold"), **self.label_style).pack(
            pady=(20, 10))
        tk.Label(self, text="Definiere hier, wie viel Zeit hinzugefügt wird.", bg=Style.BACKGROUND, fg="#aaa").pack(
            pady=(0, 20))

        # Grid Container
        grid_frm = tk.Frame(self, bg=Style.BACKGROUND)
        grid_frm.pack(fill='both', expand=True, padx=20)

        # Header
        headers = ["Aktion", "Wert (Zeit)", "Funktion"]
        for i, h in enumerate(headers):
            tk.Label(grid_frm, text=h, bg=Style.BACKGROUND, fg="#95a5a6", font=("Segoe UI", 9)).grid(row=0, column=i,
                                                                                                     sticky="w",
                                                                                                     pady=(0, 5),
                                                                                                     padx=5)

        self.event_widgets = {}
        keys = [
            ("coins", "💰 1 Coin"),
            ("like", "❤️ 1 Like"),
            ("share", "↪️ Share"),
            ("follow", "➕ Follow"),
            ("subscribe", "⭐ Abo / Sub")
        ]

        for idx, (k, name) in enumerate(keys, start=1):
            tk.Label(grid_frm, text=name, width=15, anchor='w', font=("Segoe UI", 10, "bold"), **self.label_style).grid(
                row=idx, column=0, pady=5, padx=5)

            data = self.settings.get(k, {"value": "0", "active": False})

            # Value Entry
            val_frame = tk.Frame(grid_frm, bg=Style.BACKGROUND)
            val_frame.grid(row=idx, column=1, pady=5, padx=5, sticky="w")

            e = tk.Entry(val_frame, **self.entry_style, width=8, justify='center')
            e.insert(0, data.get("value", 0))
            e.pack(side='left')
            tk.Label(val_frame, text="Sek.", bg=Style.BACKGROUND, fg="#7f8c8d").pack(side='left', padx=2)

            # Checkbox
            var = tk.BooleanVar(value=data.get("active", False))
            cb = tk.Checkbutton(grid_frm, text="Zeit hinzufügen?", variable=var,
                                bg=Style.BACKGROUND, fg="#bdc3c7", selectcolor="#2c2c2c",
                                activebackground=Style.BACKGROUND)
            cb.grid(row=idx, column=2, pady=5, padx=5, sticky="w")

            self.event_widgets[k] = {"entry": e, "var": var}

        # Footer
        tk.Button(self, text="💾 TRIGGER SPEICHERN", command=self.save_trigger,
                  bg=Style.SUCCESS, fg="white", font=("Segoe UI", 11, "bold"), pady=8, relief="flat").pack(
            side='bottom', fill='x', padx=20, pady=20)

    def save_trigger(self):
        try:
            # 1. Hole FRISCHE Settings vom Service (Merge Logik)
            current_live_settings = self.service.get_current_settings()

            # 2. Update nur die Trigger-Werte
            for k, w in self.event_widgets.items():
                current_live_settings[k] = {"value": w["entry"].get(), "active": w["var"].get()}

            # 3. Speichern
            self.service.update_settings(current_live_settings)
            show_toast(self.master, "✅ TikTok Trigger gespeichert!")
            self.destroy()
        except Exception as e:
            messagebox.showerror("Speicherfehler", str(e))


# --- 2. TIMER & GAMBIT SETTINGS (General) ---
class TimerGambitSettingsWindow(BaseSettingsWindow):
    def __init__(self, master):
        super().__init__(master, "Timer & Gambit Einstellungen", 800, 700)
        self.service = subathon_service_instance
        self.settings = self.service.get_current_settings()

        # UI Maps & Descriptions (Copy from previous code)
        self.gambit_display_map = {
            "Zeit hinzufügen (+)": "time_add",
            "Zeit abziehen (-)": "time_sub",
            "✖️ Zeit Multiplizieren": "time_multi_add",
            "➗ Zeit Teilen": "time_multi_sub",
            "❄️ Freezer Event": "event_freezer",
            "⏩ Warp (2x Speed)": "event_warp",
            "🙈 Blind (Blackout)": "event_blind",
            "🔥 Hype Mode": "event_hype",
            "💬 Nur Text": "text"
        }
        self.gambit_internal_map = {v: k for k, v in self.gambit_display_map.items()}
        self.gambit_descriptions = {
            "time_add": "Fügt dem Timer feste Sekunden hinzu.\nBeispiel Wert: 60 (fügt 1 Minute hinzu).",
            "time_sub": "Zieht Sekunden vom Timer ab.\nBeispiel Wert: 30 (zieht 30 Sekunden ab).",
            "time_multi_add": "Multipliziert die aktuelle Zeit.\nWert 1.5 = +50% Zeit | Wert 2.0 = Verdoppeln.",
            "time_multi_sub": "Teilt die aktuelle Zeit.\nWert 2.0 = Zeit halbieren.",
            "event_freezer": "Pausiert den Timer für X Sekunden.",
            "event_warp": "Timer läuft 2x so schnell ab.",
            "event_blind": "Der Stream wird schwarz/unsichtbar.",
            "event_hype": "Jede Spende zählt doppelt.",
            "text": "Zeigt nur einen Text im Overlay an."
        }

        # Notebook Styles
        style = ttk.Style()
        style.theme_use('default')
        style.configure("TNotebook", background=Style.BACKGROUND, borderwidth=0)
        style.configure("TNotebook.Tab", background="#2c3e50", foreground="#bdc3c7", padding=[15, 8],
                        font=("Segoe UI", 10))
        style.map("TNotebook.Tab", background=[("selected", Style.ACCENT_BLUE)], foreground=[("selected", "white")])

        self.notebook = ttk.Notebook(self)
        self.notebook.pack(fill='both', expand=True, padx=15, pady=15)

        # Tab 1: Timer Basis
        self.tab_timer = tk.Frame(self.notebook, bg=Style.BACKGROUND)
        self.notebook.add(self.tab_timer, text="⏱️ Timer Basis")
        self._build_timer_tab()

        # Tab 2: Events
        self.tab_events = tk.Frame(self.notebook, bg=Style.BACKGROUND)
        self.notebook.add(self.tab_events, text="⚡ Event-Dauer")
        self._build_events_tab()

        # Tab 3: Gambit
        self.tab_gambit = tk.Frame(self.notebook, bg=Style.BACKGROUND)
        self.notebook.add(self.tab_gambit, text="🎰 Gambit Roulette")
        self._build_gambit_tab()

        # Footer
        tk.Button(self, text="💾 GENERAL SETTINGS SPEICHERN", command=self.save_general,
                  bg=Style.SUCCESS, fg="white", font=("Segoe UI", 11, "bold"), pady=8, relief="flat").pack(fill='x',
                                                                                                           padx=15,
                                                                                                           pady=10)

    def _build_timer_tab(self):
        f = self.tab_timer
        tk.Label(f, text="Startzeit Konfiguration", **self.label_header).pack(anchor='w', pady=(30, 10), padx=20)

        frm_start = tk.Frame(f, bg="#2c2c2c", padx=20, pady=20)
        frm_start.pack(fill='x', padx=20)

        tk.Label(frm_start, text="Startzeit des Timers:", **self.label_style).pack(side='left')
        self.start_time = tk.Entry(frm_start, **self.entry_style, width=10, justify='center')
        self.start_time.insert(0, self.settings.get("start_time_seconds", 3600))
        self.start_time.pack(side='left', padx=10)
        tk.Label(frm_start, text="Sekunden", fg="#7f8c8d", bg="#2c2c2c").pack(side='left')

    def _build_events_tab(self):
        f = self.tab_events
        tk.Label(f, text="Dauer der Spezial-Events", **self.label_header).pack(anchor='w', pady=(15, 10), padx=20)

        self.durations = {}
        events = [("freezer", "❄️ Freezer (Pause)", 180), ("warp", "⏩ Warp (2x Speed)", 60),
                  ("blind", "🙈 Blackout", 120), ("hype", "🔥 Hype Mode", 300)]

        container = tk.Frame(f, bg="#2c2c2c", padx=20, pady=20)
        container.pack(fill='x', padx=20)

        for k, name, default in events:
            row = tk.Frame(container, bg="#2c2c2c")
            row.pack(fill='x', pady=8)
            tk.Label(row, text=name, width=25, anchor='w', bg="#2c2c2c", fg="white", font=("Segoe UI", 10)).pack(
                side='left')
            e = tk.Entry(row, **self.entry_style, width=10, justify='center')
            e.insert(0, self.settings.get(f"duration_{k}", default))
            e.pack(side='left')
            tk.Label(row, text="Sek.", bg="#2c2c2c", fg="#7f8c8d").pack(side='left', padx=5)
            self.durations[k] = e

    def _build_gambit_tab(self):
        f = self.tab_gambit
        paned = tk.PanedWindow(f, orient='horizontal', bg="#444", sashwidth=4)
        paned.pack(fill='both', expand=True, padx=10, pady=10)

        left_frame = tk.Frame(paned, bg=Style.BACKGROUND)
        paned.add(left_frame, minsize=300)
        tk.Label(left_frame, text="Ergebnisse", **self.label_header).pack(anchor='w', pady=5)

        self.tree = ttk.Treeview(left_frame, columns=("Text", "Typ", "Wert"), show='headings', selectmode='browse')
        self.tree.heading("Text", text="Text");
        self.tree.column("Text", width=120)
        self.tree.heading("Typ", text="Effekt");
        self.tree.column("Typ", width=80)
        self.tree.heading("Wert", text="Wert");
        self.tree.column("Wert", width=50)

        sb = ttk.Scrollbar(left_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=sb.set)
        self.tree.pack(side='left', fill='both', expand=True);
        sb.pack(side='right', fill='y')
        self.tree.bind("<<TreeviewSelect>>", self._on_gambit_select)

        right_frame = tk.Frame(paned, bg="#252526", padx=15, pady=15)
        paned.add(right_frame, minsize=350)
        tk.Label(right_frame, text="Editor", bg="#252526", fg="white", font=("Segoe UI", 12, "bold")).pack(anchor='w',
                                                                                                           pady=(0, 15))

        tk.Label(right_frame, text="Text:", bg="#252526", fg="#bdc3c7").pack(anchor='w')
        self.g_text = tk.Entry(right_frame, **self.entry_style);
        self.g_text.pack(fill='x', pady=2)

        tk.Label(right_frame, text="Typ:", bg="#252526", fg="#bdc3c7").pack(anchor='w')
        self.g_type_cb = ttk.Combobox(right_frame, values=list(self.gambit_display_map.keys()), state="readonly")
        self.g_type_cb.pack(fill='x', pady=2);
        self.g_type_cb.bind("<<ComboboxSelected>>", self._update_gambit_help)

        self.help_lbl = tk.Label(right_frame, text="-", bg="#252526", fg="#888", wraplength=300, justify="left")
        self.help_lbl.pack(fill='x', pady=5)

        tk.Label(right_frame, text="Wert:", bg="#252526", fg="#bdc3c7").pack(anchor='w')
        self.g_val = tk.Entry(right_frame, **self.entry_style);
        self.g_val.pack(fill='x', pady=2)

        color_row = tk.Frame(right_frame, bg="#252526");
        color_row.pack(fill='x', pady=10)
        self.g_color_btn = tk.Button(color_row, text="", width=4, relief="flat", command=self._pick_color)
        self.g_color_btn.pack(side='left', padx=5)
        self.g_color_lbl = tk.Label(color_row, text="#FFFFFF", bg="#252526", fg="white");
        self.g_color_lbl.pack(side='left')
        self.current_color = "#FFFFFF";
        self._update_color_btn("#FFFFFF")

        btn_row = tk.Frame(right_frame, bg="#252526");
        btn_row.pack(fill='x', pady=10)
        tk.Button(btn_row, text="➕ Update/Add", command=self._add_gambit, bg=Style.SUCCESS, fg="white",
                  relief="flat").pack(side='left', fill='x', expand=True, padx=2)
        tk.Button(btn_row, text="🗑️ Del", command=self._del_gambit, bg=Style.DANGER, fg="white", relief="flat").pack(
            side='left', fill='x', expand=True, padx=2)

        self._reload_gambit_list()

    def _update_gambit_help(self, e=None):
        self.help_lbl.config(text=self.gambit_descriptions.get(self.gambit_display_map.get(self.g_type_cb.get()), "-"))

    def _reload_gambit_list(self):
        for i in self.tree.get_children(): self.tree.delete(i)
        for o in self.settings.get("gambit_outcomes", []):
            self.tree.insert('', 'end',
                             values=(o.get('text'), self.gambit_internal_map.get(o.get('type'), o.get('type')),
                                     o.get('value'), o.get('color')))

    def _on_gambit_select(self, e):
        sel = self.tree.selection()
        if not sel: return
        v = self.tree.item(sel[0])['values']
        self.g_text.delete(0, 'end');
        self.g_text.insert(0, v[0])
        self.g_type_cb.set(v[1] if v[1] in self.gambit_internal_map else self.gambit_internal_map.get(v[1], ''))
        self._update_gambit_help()
        self.g_val.delete(0, 'end');
        self.g_val.insert(0, v[2])
        self._update_color_btn(v[3])

    def _update_color_btn(self, c):
        self.current_color = c;
        self.g_color_btn.config(bg=c, activebackground=c);
        self.g_color_lbl.config(text=c)

    def _pick_color(self):
        c = colorchooser.askcolor(color=self.current_color)[1]
        if c: self._update_color_btn(c)

    def _add_gambit(self):
        try:
            typ = self.gambit_display_map.get(self.g_type_cb.get())
            if not typ: raise ValueError("Typ wählen")
            obj = {"text": self.g_text.get(), "type": typ, "value": float(self.g_val.get()),
                   "color": self.current_color}
            if "gambit_outcomes" not in self.settings: self.settings["gambit_outcomes"] = []
            self.settings["gambit_outcomes"].append(obj)
            self._reload_gambit_list()
        except Exception as e:
            messagebox.showerror("Err", str(e))

    def _del_gambit(self):
        sel = self.tree.selection()
        if sel:
            del self.settings["gambit_outcomes"][self.tree.index(sel[0])]
            self._reload_gambit_list()

    def save_general(self):
        try:
            # 1. Hole FRISCHE Settings (Merge Logik)
            current_live_settings = self.service.get_current_settings()

            # 2. Update nur General Keys
            current_live_settings["start_time_seconds"] = self.start_time.get()
            for k, e in self.durations.items():
                current_live_settings[f"duration_{k}"] = e.get()
            current_live_settings["gambit_outcomes"] = self.settings.get("gambit_outcomes", [])

            # 3. Speichern
            self.service.update_settings(current_live_settings)
            show_toast(self.master, "✅ General Settings gespeichert!")
            self.destroy()
        except Exception as e:
            messagebox.showerror("Speicherfehler", str(e))


# --- LIKE CHALLENGE ---
class LikeChallengeSettingsWindow(BaseSettingsWindow):
    def __init__(self, master):
        super().__init__(master, "Like Challenge Einstellungen", 600, 450)
        self.service = like_service_instance
        tk.Label(self, text="Like Challenge Konfiguration", font=("Segoe UI", 14, "bold"), **self.label_style).pack(
            pady=(20, 10))

        try:
            self.current_settings = self.service.settings_manager.load_settings()
        except:
            self.current_settings = {"displayTextFormat": "{likes_needed} Likes",
                                     "recurringGoalExpression": "x + 33333", "initialGoals": []}

        form_frame = tk.Frame(self, bg=Style.BACKGROUND, padx=30)
        form_frame.pack(pady=10, fill='x');
        form_frame.columnconfigure(1, weight=1)

        def create_row(row, label_text, key):
            tk.Label(form_frame, text=label_text, **self.label_style, anchor='w').grid(row=row, column=0, sticky="w",
                                                                                       pady=10)
            e = tk.Entry(form_frame, **self.entry_style)
            e.insert(0, self.current_settings.get(key, ""))
            e.grid(row=row, column=1, sticky="ew", pady=10, padx=(10, 0))
            return e

        self.entries = {}
        self.entries["displayTextFormat"] = create_row(0, "Anzeigeformat (Platzhalter: {likes_needed}):",
                                                       "displayTextFormat")
        self.entries["recurringGoalExpression"] = create_row(1, "Formel für nächstes Ziel (Variable 'x'):",
                                                             "recurringGoalExpression")

        tk.Label(form_frame, text="Start-Ziele (Kommagetrennt):", **self.label_style, anchor='w').grid(row=2, column=0,
                                                                                                       sticky="w",
                                                                                                       pady=10)
        self.goals_entry = tk.Entry(form_frame, **self.entry_style)
        self.goals_entry.insert(0, ",".join(map(str, self.current_settings.get("initialGoals", []))))
        self.goals_entry.grid(row=2, column=1, sticky="ew", pady=10, padx=(10, 0))

        tk.Button(self, text="SPEICHERN", command=self.save, **{**self.btn_style, "bg": Style.SUCCESS}).pack(pady=30,
                                                                                                             fill='x',
                                                                                                             padx=30)

    def save(self):
        try:
            s = self.service.settings_manager.load_settings()
            s.update({k: self.entries[k].get() for k in self.entries})
            val = self.goals_entry.get().strip()
            s["initialGoals"] = sorted([int(x.strip()) for x in val.split(',') if x.strip()]) if val else []
            self.service.settings_manager.save_settings(s)
            messagebox.showinfo("Erfolg", "Einstellungen gespeichert!");
            self.destroy()
        except Exception as e:
            messagebox.showerror("Fehler", str(e))


# --- COMMANDS ---
class CommandsSettingsWindow(BaseSettingsWindow):
    def __init__(self, master):
        super().__init__(master, "Command Overlay Einstellungen", 800, 650)
        self.service = command_service_instance
        tk.Label(self, text="Command Overlay Konfiguration", font=("Segoe UI", 14, "bold"), **self.label_style).pack(
            pady=(15, 10))
        self.selected_command_id = None

        main_frame = tk.Frame(self, bg=Style.BACKGROUND, padx=20, pady=10);
        main_frame.pack(fill='both', expand=True)
        main_frame.columnconfigure(0, weight=1);
        main_frame.columnconfigure(1, weight=1)

        # Dauer
        settings_frame = tk.LabelFrame(main_frame, text="Allgemein", bg=Style.BACKGROUND, fg="#aaa")
        settings_frame.grid(row=0, column=0, columnspan=2, sticky="ew", pady=(0, 15))
        tk.Label(settings_frame, text="Anzeigedauer (Sek.):", **self.label_style).pack(side=tk.LEFT, padx=10, pady=10)

        try:
            self.settings = self.service.get_settings()
        except:
            self.settings = {"display_duration_seconds": 5}

        self.duration_var = tk.StringVar(value=self.settings.get("display_duration_seconds", 5))
        tk.Entry(settings_frame, textvariable=self.duration_var, **self.entry_style, width=5, justify='center').pack(
            side=tk.LEFT)
        tk.Button(settings_frame, text="Update Dauer", command=self.save_duration, bg="#444", fg="white",
                  relief="flat").pack(side=tk.LEFT, padx=10)

        # Tabelle
        tree_frame = tk.Frame(main_frame, bg=Style.BACKGROUND);
        tree_frame.grid(row=2, column=0, columnspan=2, sticky="nsew", pady=5)
        tree_frame.rowconfigure(0, weight=1);
        tree_frame.columnconfigure(0, weight=1)
        self.tree = ttk.Treeview(tree_frame, columns=('Command', 'Kosten'), show='headings', selectmode='browse',
                                 height=10)
        self.tree.heading('Command', text='Trigger Text');
        self.tree.heading('Kosten', text='Kosten')
        self.tree.column('Command', width=450);
        self.tree.column('Kosten', width=100, anchor='e')
        sb = ttk.Scrollbar(tree_frame, orient="vertical", command=self.tree.yview);
        self.tree.configure(yscrollcommand=sb.set)
        self.tree.grid(row=0, column=0, sticky="nsew");
        sb.grid(row=0, column=1, sticky="ns")
        self.tree.bind('<<TreeviewSelect>>', self.on_select)
        main_frame.rowconfigure(2, weight=1)

        # Editor
        entry_frame = tk.LabelFrame(main_frame, text="Command Bearbeiten", bg=Style.BACKGROUND, fg="#aaa", padx=10,
                                    pady=10)
        entry_frame.grid(row=3, column=0, columnspan=2, sticky="ew", pady=10);
        entry_frame.columnconfigure(1, weight=1)

        tk.Label(entry_frame, text="Text:", **self.label_style).grid(row=0, column=0, sticky="w")
        self.entry_text_var = tk.StringVar();
        tk.Entry(entry_frame, textvariable=self.entry_text_var, **self.entry_style).grid(row=0, column=1, sticky="ew",
                                                                                         padx=10, ipady=3)

        tk.Label(entry_frame, text="Kosten:", **self.label_style).grid(row=1, column=0, sticky="w", pady=10)
        self.entry_costs_var = tk.StringVar();
        tk.Entry(entry_frame, textvariable=self.entry_costs_var, **self.entry_style, width=15).grid(row=1, column=1,
                                                                                                    sticky="w", padx=10,
                                                                                                    ipady=3)
        self.superfan_var = tk.BooleanVar()
        tk.Checkbutton(entry_frame, text="Nur für Superfans ⭐", variable=self.superfan_var, bg=Style.BACKGROUND,
                       fg="white", selectcolor="#444", activebackground=Style.BACKGROUND).grid(row=1, column=1,
                                                                                               sticky="e")

        # Buttons
        btn_frame = tk.Frame(main_frame, bg=Style.BACKGROUND);
        btn_frame.grid(row=4, column=0, columnspan=2, sticky="ew", pady=10)
        tk.Button(btn_frame, text="➕ Hinzufügen", command=self.add, **{**self.btn_style, "bg": Style.SUCCESS}).pack(
            side=tk.LEFT, padx=(0, 5))
        self.edit_button = tk.Button(btn_frame, text="✏️ Ändern", command=self.edit,
                                     **{**self.btn_style, "bg": "#f39c12"}, state="disabled");
        self.edit_button.pack(side=tk.LEFT, padx=5)
        self.delete_button = tk.Button(btn_frame, text="🗑️ Löschen", command=self.delete,
                                       **{**self.btn_style, "bg": Style.DANGER}, state="disabled");
        self.delete_button.pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text="▶ Test Fire", command=self.fire, **{**self.btn_style, "bg": Style.ACCENT_BLUE}).pack(
            side=tk.RIGHT)

        self.load_commands()

    def save_duration(self):
        try:
            self.service.save_settings({"display_duration_seconds": int(self.duration_var.get())}); show_toast(self,
                                                                                                               "Dauer gespeichert!")
        except:
            messagebox.showerror("Fehler", "Zahl erwartet.")

    def load_commands(self):
        for i in self.tree.get_children(): self.tree.delete(i)
        for c in self.service.get_all_commands():
            d = ("⭐ " + c.get('text', '')) if c.get('is_superfan') else c.get('text', '')
            self.tree.insert('', 'end', iid=c.get('id') or str(uuid.uuid4()), values=(d, c.get('costs', '')))
        self.clear_selection()

    def on_select(self, e):
        sel = self.tree.selection()
        if not sel: return
        self.selected_command_id = sel[0]
        c = next((x for x in self.service.get_all_commands() if x.get('id') == self.selected_command_id), None)
        if c:
            self.entry_text_var.set(c.get('text', ''));
            self.entry_costs_var.set(c.get('costs', ''));
            self.superfan_var.set(c.get('is_superfan', False))
            self.edit_button.config(state="normal");
            self.delete_button.config(state="normal")

    def clear_selection(self):
        self.selected_command_id = None;
        self.entry_text_var.set("");
        self.entry_costs_var.set("");
        self.superfan_var.set(False)
        self.edit_button.config(state="disabled");
        self.delete_button.config(state="disabled")

    def add(self):
        try:
            self.service.add_command(self.entry_text_var.get(), self.entry_costs_var.get(),
                                     self.superfan_var.get()); self.load_commands()
        except Exception as e:
            messagebox.showerror("Fehler", str(e))

    def edit(self):
        if self.selected_command_id:
            try:
                self.service.update_command(self.selected_command_id, self.entry_text_var.get(),
                                            self.entry_costs_var.get(), self.superfan_var.get()); self.load_commands()
            except Exception as e:
                messagebox.showerror("Fehler", str(e))

    def delete(self):
        if self.selected_command_id and messagebox.askyesno("Löschen", "Sicher?"):
            self.service.delete_command(self.selected_command_id);
            self.load_commands()

    def fire(self):
        if messagebox.askyesno("Start", "Auslösen?"):
            from config import COMMANDS_TRIGGER_ENDPOINT, BASE_HOST, BASE_PORT;
            import requests
            try:
                requests.post(f"http://{BASE_HOST}:{BASE_PORT}{COMMANDS_TRIGGER_ENDPOINT}", timeout=1)
            except:
                pass