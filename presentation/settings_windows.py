import tkinter as tk
from tkinter import messagebox, font, ttk
import sys

# Importiere Service Layer
from services.service_provider import (
    like_service_instance,
    subathon_service_instance,
    command_service_instance
)

from config import Style
from presentation.ui_elements import show_toast
from utils import server_log


# --- Allgemeine Basisklasse für Einstellungsfenster ---
class BaseSettingsWindow(tk.Toplevel):
    def __init__(self, master, title, width=550, height=450):
        super().__init__(master)
        self.title(title)
        self.geometry(f"{width}x{height}")
        self.transient(master)
        self.grab_set()
        self.resizable(False, False)
        self.configure(bg=Style.BACKGROUND)

        # Zentrieren des Fensters
        self.update_idletasks()
        w = self.winfo_width()
        h = self.winfo_height()
        x = master.winfo_x() + (master.winfo_width() // 2) - (w // 2)
        y = master.winfo_y() + (master.winfo_height() // 2) - (h // 2)
        self.geometry(f'+{x}+{y}')

        self.columnconfigure(0, weight=1)

        # Styles für Labels/Buttons
        self.label_style = {"bg": Style.BACKGROUND, "fg": Style.FOREGROUND,
                            "font": font.Font(family=Style.FONT_FAMILY, size=11)}
        self.entry_style = {"font": font.Font(family=Style.FONT_FAMILY, size=11),
                            "bg": Style.WIDGET_BG, "fg": "white", "insertbackground": "white", "relief": tk.FLAT}
        self.check_style = {"bg": "#222222", "fg": "white", "selectcolor": "#444444",
                            "activebackground": "#222222", "activeforeground": "white",
                            "font": font.Font(family=Style.FONT_FAMILY, size=10)}
        self.button_style = {"font": font.Font(family=Style.FONT_FAMILY, size=11, weight="bold"), "relief": tk.FLAT,
                             "bg": Style.ACCENT_PURPLE, "fg": "white", "activebackground": Style.WIDGET_HOVER,
                             "pady": 8, "cursor": "hand2"}

        self.protocol("WM_DELETE_WINDOW", self.on_close)
        self.master = master

    def add_title(self, text, color=Style.ACCENT_BLUE):
        tk.Label(self, text=text, bg=Style.BACKGROUND, fg=color,
                 font=font.Font(family=Style.FONT_FAMILY, size=16, weight="bold")).pack(pady=(15, 10))

    def on_close(self):
        self.destroy()
        self.master.grab_release()


# --- Subathon Settings Window (UX OPTIMIERT) ---
class SubathonSettingsWindow(BaseSettingsWindow):
    def __init__(self, master):
        super().__init__(master, "Subathon Timer Einstellungen", 600, 680)
        self.service = subathon_service_instance
        self.add_title("Subathon Konfiguration")

        try:
            self.current_settings = self.service.get_current_settings()
        except Exception as e:
            self.current_settings = {}

        self.widgets = {}

        # Hauptcontainer mit Padding
        main_frame = tk.Frame(self, bg=Style.BACKGROUND, padx=20, pady=10)
        main_frame.pack(fill='both', expand=True)

        # --- SEKTION 1: ALLGEMEIN ---
        # Wir nutzen LabelFrames für Gruppierung (bessere Übersicht)
        group_general = tk.LabelFrame(main_frame, text=" Basis Einstellungen ", bg=Style.BACKGROUND,
                                      fg=Style.ACCENT_BLUE,
                                      font=("Arial", 10, "bold"), bd=1, relief=tk.GROOVE)
        group_general.pack(fill="x", pady=10, ipady=5)

        # Startzeit
        frame_start = tk.Frame(group_general, bg=Style.BACKGROUND)
        frame_start.pack(fill="x", padx=10, pady=5)
        tk.Label(frame_start, text="Startzeit (Sekunden):", **self.label_style, width=20, anchor="w").pack(side=tk.LEFT)

        self.start_time_entry = tk.Entry(frame_start, **self.entry_style, width=10)
        self.start_time_entry.insert(0, self.current_settings.get("start_time_seconds", "3600"))
        self.start_time_entry.pack(side=tk.LEFT, padx=5)

        # Live-Rechner Label (z.B. "1.0 Std")
        self.calc_label = tk.Label(frame_start, text="= 1.0 Std", bg=Style.BACKGROUND, fg=Style.TEXT_MUTED,
                                   font=("Arial", 9))
        self.calc_label.pack(side=tk.LEFT, padx=5)
        # Bindung für Live-Update
        self.start_time_entry.bind("<KeyRelease>", self._update_calc_label)
        self._update_calc_label()  # Initial aufrufen

        # Animationszeit
        frame_anim = tk.Frame(group_general, bg=Style.BACKGROUND)
        frame_anim.pack(fill="x", padx=10, pady=5)
        tk.Label(frame_anim, text="Info-Wechsel (Sek.):", **self.label_style, width=20, anchor="w").pack(side=tk.LEFT)
        self.anim_time_entry = tk.Entry(frame_anim, **self.entry_style, width=10)
        self.anim_time_entry.insert(0, self.current_settings.get("animations_time", "5"))
        self.anim_time_entry.pack(side=tk.LEFT, padx=5)

        # --- SEKTION 2: TIKTOK EVENTS ---
        group_tiktok = tk.LabelFrame(main_frame, text=" TikTok Events (Zeit hinzufügen) ", bg=Style.BACKGROUND,
                                     fg=Style.ACCENT_PURPLE,
                                     font=("Arial", 10, "bold"), bd=1, relief=tk.GROOVE)
        group_tiktok.pack(fill="x", pady=10, ipady=5)

        self.event_keys = [
            ("coins", "1 Coin / Rose:"),
            ("subscribe", "TikTok Abo:"),
            ("follow", "Neuer Follower:"),
            ("share", "Stream geteilt:"),
        ]
        self._build_event_rows(group_tiktok, self.event_keys)

        # --- SEKTION 3: EXTERNE EVENTS ---
        group_twitch = tk.LabelFrame(main_frame, text=" Twitch & Extern ", bg=Style.BACKGROUND, fg="#a970ff",
                                     # Twitch Lila
                                     font=("Arial", 10, "bold"), bd=1, relief=tk.GROOVE)
        group_twitch.pack(fill="x", pady=10, ipady=5)

        self.twitch_keys = [("twitch_sub", "Twitch Sub:")]
        self._build_event_rows(group_twitch, self.twitch_keys)

        # --- FOOTER ---
        tk.Button(main_frame, text="EINSTELLUNGEN SPEICHERN", command=self.save_settings, **self.button_style).pack(
            side=tk.BOTTOM, fill='x', pady=10)

    def _build_event_rows(self, parent, keys):
        """Erzeugt die Eingabezeilen dynamisch und sauber ausgerichtet."""
        for key, display_text in keys:
            default_val = {"value": "0", "active": False}
            event_data = self.current_settings.get(key, default_val)

            # Bereinige den Wert (entferne " Seconds" falls vorhanden aus alten Configs)
            val_str = str(event_data.get("value", "0")).split()[0]

            row = tk.Frame(parent, bg=Style.BACKGROUND)
            row.pack(fill='x', padx=10, pady=4)

            # Label
            tk.Label(row, text=display_text, **self.label_style, width=18, anchor="w").pack(side=tk.LEFT)

            # Input (+ Label "Sek.")
            entry = tk.Entry(row, **self.entry_style, width=8, justify="center")
            entry.insert(0, val_str)
            entry.pack(side=tk.LEFT, padx=(0, 5))

            tk.Label(row, text="Sek.", bg=Style.BACKGROUND, fg="#888888", font=("Arial", 9)).pack(side=tk.LEFT)

            # Checkbox (Rechtsbündig durch Frame-Trick oder pack side right)
            # Wir nutzen einen Container für den Style
            chk_frame = tk.Frame(row, bg="#222222", padx=5, pady=2, relief=tk.FLAT)
            chk_frame.pack(side=tk.RIGHT)

            var = tk.BooleanVar(value=event_data.get("active", False))
            chk = tk.Checkbutton(chk_frame, text="Aktiv", variable=var, **self.check_style, cursor="hand2")
            chk.pack()

            self.widgets[key] = {"value_entry": entry, "active_var": var}

    def _update_calc_label(self, event=None):
        """Rechnet Sekunden live in Stunden/Minuten um."""
        try:
            sec = int(self.start_time_entry.get())
            if sec < 60:
                txt = f"= {sec} Sek"
            elif sec < 3600:
                txt = f"= {sec / 60:.1f} Min"
            else:
                txt = f"= {sec / 3600:.1f} Std"
            self.calc_label.config(text=txt, fg=Style.SUCCESS)
        except ValueError:
            self.calc_label.config(text="Ungültig", fg=Style.DANGER)

    def save_settings(self):
        try:
            new_settings = self.current_settings.copy()

            # Basiswerte validieren
            start_time = int(self.start_time_entry.get())
            anim_time = float(self.anim_time_entry.get())

            new_settings["start_time_seconds"] = str(start_time)
            new_settings["animations_time"] = str(anim_time)

            # Events speichern
            for key, _ in self.event_keys + self.twitch_keys:
                widgets = self.widgets[key]
                raw_val = widgets["value_entry"].get()

                # Validierung: Ist es eine Zahl?
                float(raw_val)  # Wirft Error wenn keine Zahl

                # Wir speichern nur die Zahl, das "Seconds" ist implizit im Service
                new_settings[key] = {
                    "value": raw_val,
                    "active": widgets["active_var"].get()
                }

            self.service.update_settings(new_settings)
            messagebox.showinfo("Erfolg", "Einstellungen gespeichert!\n(Timer Reset erforderlich für neue Startzeit)")
            self.on_close()

        except ValueError:
            messagebox.showerror("Eingabefehler", "Bitte nur gültige Zahlen eingeben (keine Buchstaben).")
        except Exception as e:
            messagebox.showerror("Fehler", f"Speichern fehlgeschlagen: {e}")


# --- Like Challenge Settings Window (Bereinigt) ---
class LikeChallengeSettingsWindow(BaseSettingsWindow):
    def __init__(self, master):
        super().__init__(master, "Like Challenge Einstellungen", 600, 400)
        self.service = like_service_instance
        self.add_title("Like Challenge Ziel-Konfiguration", color=Style.ACCENT_PURPLE)
        try:
            self.current_settings = self.service.settings_manager.load_settings()
        except Exception:
            self.current_settings = {"displayTextFormat": "{likes_needed} Likes",
                                     "recurringGoalExpression": "x + 33333", "initialGoals": []}

        form_frame = tk.Frame(self, bg=Style.BACKGROUND, padx=20)
        form_frame.pack(pady=10, fill='x')
        form_frame.columnconfigure(1, weight=1)

        fields = [
            ("Anzeigeformat ({likes_needed}):", "displayTextFormat", 0),
            ("Rekursive Zielformel (mit 'x'):", "recurringGoalExpression", 1),
        ]
        self.entries = {}
        for i, (label_text, key, row) in enumerate(fields):
            tk.Label(form_frame, text=label_text, **self.label_style).grid(row=row, column=0, sticky="w", pady=10,
                                                                           padx=5)
            entry = tk.Entry(form_frame, **self.entry_style)
            entry.insert(0, self.current_settings.get(key, ""))
            entry.grid(row=row, column=1, sticky="ew", pady=10, padx=5, ipady=3)
            self.entries[key] = entry

        tk.Label(form_frame, text="Initiale Ziele (z.B. 100, 500, 1000):", **self.label_style).grid(row=2, column=0,
                                                                                                    sticky="w", pady=10,
                                                                                                    padx=5)
        initial_goals_str = ", ".join(map(str, self.current_settings.get("initialGoals", [])))
        self.goals_entry = tk.Entry(form_frame, **self.entry_style)
        self.goals_entry.insert(0, initial_goals_str)
        self.goals_entry.grid(row=2, column=1, sticky="ew", pady=10, padx=5, ipady=3)

        tk.Button(self, text="SPEICHERN", command=self.save_settings, **self.button_style).pack(pady=30, fill='x',
                                                                                                padx=20)

    def save_settings(self):
        try:
            raw_goals = self.goals_entry.get().split(',')
            initial_goals = sorted([int(g.strip()) for g in raw_goals if g.strip()])

            settings = self.service.settings_manager.load_settings()
            settings["displayTextFormat"] = self.entries["displayTextFormat"].get()
            settings["recurringGoalExpression"] = self.entries["recurringGoalExpression"].get()
            settings["initialGoals"] = initial_goals

            self.service.settings_manager.save_settings(settings)
            messagebox.showinfo("Erfolg", "Like Einstellungen gespeichert!")
            self.on_close()
        except ValueError:
            messagebox.showerror("Fehler", "Ziele müssen ganze Zahlen sein.")
        except Exception as e:
            messagebox.showerror("Fehler", f"Speichern fehlgeschlagen: {e}")


# --- Commands Settings Window (Standard) ---
class CommandsSettingsWindow(BaseSettingsWindow):
    def __init__(self, master):
        super().__init__(master, "Command Overlay Einstellungen", 750, 600)
        self.service = command_service_instance
        self.add_title("Command Overlay Konfiguration")
        self.selected_command_id = None

        main_frame = tk.Frame(self, bg=Style.BACKGROUND, padx=20, pady=10)
        main_frame.pack(fill='both', expand=True)
        main_frame.columnconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)

        # Dauer
        settings_frame = tk.Frame(main_frame, bg=Style.BACKGROUND)
        settings_frame.grid(row=0, column=0, columnspan=2, sticky="ew", pady=(0, 15))
        tk.Label(settings_frame, text="Anzeigedauer (Sek.):", **self.label_style).pack(side=tk.LEFT, padx=(0, 10))
        try:
            self.settings = self.service.get_settings()
        except:
            self.settings = {"display_duration_seconds": 5}
        self.duration_var = tk.StringVar(value=self.settings.get("display_duration_seconds", 5))
        tk.Entry(settings_frame, textvariable=self.duration_var, **self.entry_style, width=10).pack(side=tk.LEFT)
        tk.Button(settings_frame, text="Speichern", command=self.save_duration_settings, **self.button_style).pack(
            side=tk.LEFT, padx=(10, 0))

        # Tabelle
        tree_frame = tk.Frame(main_frame, bg=Style.BACKGROUND)
        tree_frame.grid(row=2, column=0, columnspan=2, sticky="nsew", pady=(5, 10))
        tree_frame.rowconfigure(0, weight=1)
        tree_frame.columnconfigure(0, weight=1)

        style = ttk.Style()
        style.theme_use("default")
        style.configure("Treeview", background="#222222", foreground="white", fieldbackground="#222222", borderwidth=0,
                        rowheight=25)
        style.configure("Treeview.Heading", background="#333333", foreground="white", font=("Arial", 10, "bold"),
                        borderwidth=1)
        style.map("Treeview", background=[('selected', Style.ACCENT_PURPLE)])

        self.tree = ttk.Treeview(tree_frame, columns=('Command', 'Kosten'), show='headings', selectmode='browse')
        self.tree.heading('Command', text='Trigger (Text)')
        self.tree.heading('Kosten', text='Kosten')
        self.tree.column('Command', anchor='w', width=450)
        self.tree.column('Kosten', anchor='e', width=100)

        sb = ttk.Scrollbar(tree_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=sb.set)
        self.tree.grid(row=0, column=0, sticky="nsew")
        sb.grid(row=0, column=1, sticky="ns")
        self.tree.bind('<<TreeviewSelect>>', self.on_item_select)
        main_frame.rowconfigure(2, weight=1)

        # Eingabe
        entry_frame = tk.Frame(main_frame, bg=Style.BACKGROUND)
        entry_frame.grid(row=3, column=0, columnspan=2, sticky="ew", pady=(10, 10))
        entry_frame.columnconfigure(0, weight=1)

        tk.Label(entry_frame, text="Command Text:", **self.label_style).grid(row=0, column=0, sticky="w")
        self.entry_text_var = tk.StringVar()
        tk.Entry(entry_frame, textvariable=self.entry_text_var, **self.entry_style).grid(row=1, column=0, sticky="ew",
                                                                                         padx=(0, 10), ipady=3)

        tk.Label(entry_frame, text="Kosten:", **self.label_style).grid(row=0, column=1, sticky="w")
        self.entry_costs_var = tk.StringVar()
        tk.Entry(entry_frame, textvariable=self.entry_costs_var, **self.entry_style, width=15).grid(row=1, column=1,
                                                                                                    sticky="w", ipady=3)

        # Buttons
        btn_frame = tk.Frame(main_frame, bg=Style.BACKGROUND)
        btn_frame.grid(row=4, column=0, columnspan=2, sticky="ew", pady=(10, 0))

        ab_style = self.button_style.copy();
        ab_style['bg'] = Style.SUCCESS
        tk.Button(btn_frame, text="HINZUFÜGEN", command=self.add_command, **ab_style).pack(side=tk.LEFT, padx=(0, 5))

        self.edit_button = tk.Button(btn_frame, text="ÄNDERN", command=self.edit_command, **self.button_style,
                                     state="disabled")
        self.edit_button.pack(side=tk.LEFT, padx=5)

        db_style = self.button_style.copy();
        db_style['bg'] = Style.DANGER
        self.delete_button = tk.Button(btn_frame, text="LÖSCHEN", command=self.delete_command, **db_style,
                                       state="disabled")
        self.delete_button.pack(side=tk.LEFT, padx=5)

        fb_style = self.button_style.copy();
        fb_style['bg'] = Style.ACCENT_BLUE
        tk.Button(btn_frame, text="▶ FIRE SEQUENZ", command=self.fire_command, **fb_style).pack(side=tk.RIGHT)

        self.load_commands()

    # (Logik Methoden bleiben gleich wie zuvor)
    def save_duration_settings(self):
        try:
            d = int(self.duration_var.get())
            if d <= 0: raise ValueError
            self.service.save_settings({"display_duration_seconds": d})
            show_toast(self, "Gespeichert!")
        except:
            messagebox.showerror("Fehler", "Ungültige Zahl.")

    def load_commands(self):
        for item in self.tree.get_children(): self.tree.delete(item)
        try:
            for cmd in self.service.get_all_commands():
                self.tree.insert('', 'end', iid=cmd['id'], values=(cmd.get('text', ''), cmd.get('costs', '')))
            self.clear_selection()
        except Exception as e:
            messagebox.showerror("Fehler", str(e))

    def on_item_select(self, event):
        sel = self.tree.selection()
        if not sel: return
        self.selected_command_id = sel[0]
        vals = self.tree.item(self.selected_command_id, 'values')
        if vals:
            self.entry_text_var.set(vals[0])
            self.entry_costs_var.set(vals[1])
            self.edit_button.config(state="normal")
            self.delete_button.config(state="normal")

    def clear_selection(self):
        if self.tree.selection(): self.tree.selection_remove(self.tree.selection())
        self.selected_command_id = None
        self.entry_text_var.set("")
        self.entry_costs_var.set("")
        self.edit_button.config(state="disabled")
        self.delete_button.config(state="disabled")

    def add_command(self):
        t, c = self.entry_text_var.get(), self.entry_costs_var.get()
        if not t or not c: return
        try:
            self.service.add_command(t, c)
            self.load_commands()
        except Exception as e:
            messagebox.showerror("Fehler", str(e))

    def edit_command(self):
        if not self.selected_command_id: return
        t, c = self.entry_text_var.get(), self.entry_costs_var.get()
        if not t or not c: return
        try:
            self.service.update_command(self.selected_command_id, t, c)
            self.load_commands()
        except Exception as e:
            messagebox.showerror("Fehler", str(e))

    def delete_command(self):
        if not self.selected_command_id: return
        if not messagebox.askyesno("Bestätigen", "Löschen?"): return
        try:
            self.service.delete_command(self.selected_command_id)
            self.load_commands()
        except Exception as e:
            messagebox.showerror("Fehler", str(e))

    def fire_command(self):
        if not messagebox.askyesno("Starten", "Sequenz starten?"): return
        try:
            requests.post(BASE_URL.rstrip('/') + COMMANDS_TRIGGER_ENDPOINT, timeout=3)
            show_toast(self.master, "Gestartet!")
        except Exception as e:
            messagebox.showerror("Fehler", str(e))