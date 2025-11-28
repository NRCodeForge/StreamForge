import tkinter as tk
from tkinter import messagebox, font, ttk
import sys

from services.service_provider import (
    like_service_instance,
    subathon_service_instance,
    command_service_instance
)
from config import Style
from presentation.ui_elements import show_toast
from utils import server_log


class BaseSettingsWindow(tk.Toplevel):
    def __init__(self, master, title, width=550, height=450):
        super().__init__(master)
        self.title(title)
        self.geometry(f"{width}x{height}")
        self.transient(master)
        self.grab_set()
        self.resizable(False, False)
        self.configure(bg=Style.BACKGROUND)

        self.update_idletasks()
        w, h = self.winfo_width(), self.winfo_height()
        x = master.winfo_x() + (master.winfo_width() // 2) - (w // 2)
        y = master.winfo_y() + (master.winfo_height() // 2) - (h // 2)
        self.geometry(f'+{x}+{y}')

        self.label_style = {"bg": Style.BACKGROUND, "fg": Style.FOREGROUND,
                            "font": font.Font(family=Style.FONT_FAMILY, size=11)}
        self.entry_style = {"font": font.Font(family=Style.FONT_FAMILY, size=11), "bg": Style.WIDGET_BG, "fg": "white",
                            "insertbackground": "white", "relief": tk.FLAT}
        # Checkbox Style (Dunkel)
        self.check_style = {"bg": "#222222", "fg": "white", "selectcolor": "#444444", "activebackground": "#222222",
                            "activeforeground": "white", "font": font.Font(family=Style.FONT_FAMILY, size=9)}
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


class SubathonSettingsWindow(BaseSettingsWindow):
    def __init__(self, master):
        super().__init__(master, "Subathon Timer Einstellungen", 650, 750)
        self.service = subathon_service_instance
        self.add_title("Subathon Konfiguration")

        try:
            self.current_settings = self.service.get_current_settings()
        except:
            self.current_settings = {}

        self.widgets = {}

        main_frame = tk.Frame(self, bg=Style.BACKGROUND, padx=20, pady=10)
        main_frame.pack(fill='both', expand=True)

        # --- BASIS ---
        group_general = tk.LabelFrame(main_frame, text=" Basis ", bg=Style.BACKGROUND, fg=Style.ACCENT_BLUE,
                                      font=("Arial", 10, "bold"), bd=1, relief=tk.GROOVE)
        group_general.pack(fill="x", pady=10, ipady=5)

        self._add_general_input(group_general, "Startzeit (Sek):", "start_time_seconds", "3600", live_calc=True)
        self._add_general_input(group_general, "Info-Wechsel (Sek):", "animations_time", "5")

        # --- TIKTOK EVENTS ---
        group_tiktok = tk.LabelFrame(main_frame, text=" TikTok Events ", bg=Style.BACKGROUND, fg=Style.ACCENT_PURPLE,
                                     font=("Arial", 10, "bold"), bd=1, relief=tk.GROOVE)
        group_tiktok.pack(fill="x", pady=10, ipady=5)

        # Header Zeile mit Beschriftungen
        self._add_header_row(group_tiktok)

        self.event_keys = [
            ("coins", "1 Coin / Rose:"),
            ("subscribe", "TikTok Abo:"),
            ("follow", "Neuer Follow:"),
            ("share", "Teilen:"),
            ("like", "1 Like:"),
            ("chat", "1 Chat Nachricht:")
        ]
        self._build_event_rows(group_tiktok, self.event_keys)

        # --- TWITCH / EXTERN ---
        group_twitch = tk.LabelFrame(main_frame, text=" Twitch & Extern ", bg=Style.BACKGROUND, fg="#a970ff",
                                     font=("Arial", 10, "bold"), bd=1, relief=tk.GROOVE)
        group_twitch.pack(fill="x", pady=10, ipady=5)

        # Auch hier Header, damit es konsistent ist
        self._add_header_row(group_twitch)

        self.twitch_keys = [("twitch_sub", "Twitch Sub:")]
        self._build_event_rows(group_twitch, self.twitch_keys)

        # Footer
        tk.Button(main_frame, text="EINSTELLUNGEN SPEICHERN", command=self.save_settings, **self.button_style).pack(
            side=tk.BOTTOM, fill='x', pady=10)

    def _add_general_input(self, parent, label_text, key, default, live_calc=False):
        frame = tk.Frame(parent, bg=Style.BACKGROUND)
        frame.pack(fill="x", padx=10, pady=5)
        tk.Label(frame, text=label_text, **self.label_style, width=20, anchor="w").pack(side=tk.LEFT)

        entry = tk.Entry(frame, **self.entry_style, width=10)
        entry.insert(0, self.current_settings.get(key, default))
        entry.pack(side=tk.LEFT, padx=5)

        if live_calc:
            self.start_time_entry = entry
            self.calc_label = tk.Label(frame, text="", bg=Style.BACKGROUND, fg=Style.TEXT_MUTED, font=("Arial", 9))
            self.calc_label.pack(side=tk.LEFT, padx=5)
            entry.bind("<KeyRelease>", self._update_calc_label)
            self._update_calc_label()
        else:
            self.anim_time_entry = entry

    def _add_header_row(self, parent):
        """Fügt die Spaltenüberschriften Add | Timer | Show hinzu."""
        row = tk.Frame(parent, bg=Style.BACKGROUND)
        row.pack(fill='x', padx=10, pady=(5, 0))

        # Platzhalter für das Label links (ca. 18 chars breit)
        tk.Label(row, text="", bg=Style.BACKGROUND, width=18).pack(side=tk.LEFT)

        # Header "Add" (über dem Input Feld)
        tk.Label(row, text="Add", bg=Style.BACKGROUND, fg="#888888", font=("Arial", 8, "bold"), width=10,
                 anchor="c").pack(side=tk.LEFT)

        # Header "Timer" (über Active Checkbox)
        # width=6 passt ungefähr zur Checkbox
        tk.Label(row, text="Timer", bg=Style.BACKGROUND, fg="#888888", font=("Arial", 8, "bold"), width=6).pack(
            side=tk.LEFT, padx=(5, 0))

        # Header "Show" (über Visible Checkbox)
        tk.Label(row, text="Show", bg=Style.BACKGROUND, fg="#888888", font=("Arial", 8, "bold"), width=6).pack(
            side=tk.LEFT)

    def _build_event_rows(self, parent, keys):
        for key, display_text in keys:
            default_val = {"value": "0", "active": False, "visible": True}
            data = self.current_settings.get(key, default_val)
            val_str = str(data.get("value", "0")).split()[0]

            row = tk.Frame(parent, bg=Style.BACKGROUND)
            row.pack(fill='x', padx=10, pady=2)

            # Label (Name)
            tk.Label(row, text=display_text, **self.label_style, width=18, anchor="w").pack(side=tk.LEFT)

            # Value Input ("Add")
            entry = tk.Entry(row, **self.entry_style, width=6, justify="center")
            entry.insert(0, val_str)
            entry.pack(side=tk.LEFT)
            tk.Label(row, text="s", bg=Style.BACKGROUND, fg="#666666").pack(side=tk.LEFT, padx=(2, 10))

            # Checkboxen Container
            chk_frame = tk.Frame(row, bg="#222222", padx=2, pady=1)
            chk_frame.pack(side=tk.LEFT)

            # 1. Timer Active Checkbox
            var_active = tk.BooleanVar(value=data.get("active", False))
            c1 = tk.Checkbutton(chk_frame, variable=var_active, **self.check_style)
            c1.pack(side=tk.LEFT, padx=7)  # Padding angepasst für Header Alignment

            # 2. Visible Checkbox
            var_visible = tk.BooleanVar(value=data.get("visible", True))
            c2 = tk.Checkbutton(chk_frame, variable=var_visible, **self.check_style)
            c2.pack(side=tk.LEFT, padx=7)

            self.widgets[key] = {"value_entry": entry, "active_var": var_active, "visible_var": var_visible}

    def _update_calc_label(self, event=None):
        try:
            sec = int(self.start_time_entry.get())
            if sec < 3600:
                txt = f"= {sec / 60:.1f} Min"
            else:
                txt = f"= {sec / 3600:.1f} Std"
            self.calc_label.config(text=txt, fg=Style.SUCCESS)
        except:
            self.calc_label.config(text="...", fg=Style.DANGER)

    def save_settings(self):
        try:
            new_s = self.current_settings.copy()
            new_s["start_time_seconds"] = self.start_time_entry.get()
            new_s["animations_time"] = self.anim_time_entry.get()

            for key, _ in self.event_keys + self.twitch_keys:
                w = self.widgets[key]
                float(w["value_entry"].get())  # Validierung
                new_s[key] = {
                    "value": w["value_entry"].get(),
                    "active": w["active_var"].get(),
                    "visible": w["visible_var"].get()
                }
            self.service.update_settings(new_s)
            messagebox.showinfo("Gespeichert", "Einstellungen übernommen!")
            self.on_close()
        except ValueError:
            messagebox.showerror("Eingabefehler", "Bitte nur gültige Zahlen eingeben.")
        except Exception as e:
            messagebox.showerror("Fehler", f"Speichern fehlgeschlagen: {e}")


# ... (LikeChallengeSettingsWindow und CommandsSettingsWindow unverändert lassen)
class LikeChallengeSettingsWindow(BaseSettingsWindow):
    def __init__(self, master):
        super().__init__(master, "Like Challenge Einstellungen", 600, 400)
        self.service = like_service_instance
        self.add_title("Like Challenge Ziel-Konfiguration", color=Style.ACCENT_PURPLE)
        try:
            self.current_settings = self.service.settings_manager.load_settings()
        except:
            self.current_settings = {"displayTextFormat": "{likes_needed} Likes",
                                     "recurringGoalExpression": "x + 33333", "initialGoals": []}
        form_frame = tk.Frame(self, bg=Style.BACKGROUND, padx=20)
        form_frame.pack(pady=10, fill='x');
        form_frame.columnconfigure(1, weight=1)
        fields = [("Anzeigeformat ({likes_needed}):", "displayTextFormat"),
                  ("Rekursive Zielformel (mit 'x'):", "recurringGoalExpression")]
        self.entries = {}
        for i, (txt, key) in enumerate(fields):
            tk.Label(form_frame, text=txt, **self.label_style).grid(row=i, column=0, sticky="w", pady=10);
            e = tk.Entry(form_frame, **self.entry_style);
            e.insert(0, self.current_settings.get(key, ""));
            e.grid(row=i, column=1, sticky="ew", pady=10);
            self.entries[key] = e
        tk.Label(form_frame, text="Ziele (Kommagetrennt):", **self.label_style).grid(row=2, column=0, sticky="w",
                                                                                     pady=10)
        self.goals_entry = tk.Entry(form_frame, **self.entry_style);
        self.goals_entry.insert(0, ",".join(map(str, self.current_settings.get("initialGoals", []))));
        self.goals_entry.grid(row=2, column=1, sticky="ew", pady=10)
        tk.Button(self, text="SPEICHERN", command=self.save, **self.button_style).pack(pady=30, fill='x', padx=20)

    def save(self):
        try:
            s = self.service.settings_manager.load_settings()
            s.update({k: self.entries[k].get() for k in self.entries})
            s["initialGoals"] = sorted([int(x.strip()) for x in self.goals_entry.get().split(',') if x.strip()])
            self.service.settings_manager.save_settings(s);
            messagebox.showinfo("OK", "Gespeichert!");
            self.on_close()
        except Exception as e:
            messagebox.showerror("Fehler", str(e))


# --- Commands Settings Window ---
class CommandsSettingsWindow(BaseSettingsWindow):
    def __init__(self, master):
        super().__init__(master, "Command Overlay Einstellungen", 750, 600)
        self.service = command_service_instance
        self.add_title("Command Overlay Konfiguration")

        self.selected_command_id = None

        # Hauptcontainer
        main_frame = tk.Frame(self, bg=Style.BACKGROUND, padx=20, pady=10)
        main_frame.pack(fill='both', expand=True)
        main_frame.columnconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)

        # --- SEKTION 1: DAUER ---
        settings_frame = tk.Frame(main_frame, bg=Style.BACKGROUND)
        settings_frame.grid(row=0, column=0, columnspan=2, sticky="ew", pady=(0, 15))

        tk.Label(settings_frame, text="Anzeigedauer pro Command (Sek.):", **self.label_style).pack(side=tk.LEFT,
                                                                                                   padx=(0, 10))

        try:
            self.settings = self.service.get_settings()
        except Exception as e:
            server_log.error(f"Settings Fehler: {e}")
            self.settings = {"display_duration_seconds": 5}

        self.duration_var = tk.StringVar(value=self.settings.get("display_duration_seconds", 5))
        tk.Entry(settings_frame, textvariable=self.duration_var, **self.entry_style, width=10).pack(side=tk.LEFT)

        tk.Button(settings_frame, text="Speichern", command=self.save_duration_settings, **self.button_style).pack(
            side=tk.LEFT, padx=(10, 0))

        # Trennlinie
        tk.Frame(main_frame, height=1, bg="#444444").grid(row=1, column=0, columnspan=2, sticky="ew", pady=(10, 15))

        # --- SEKTION 2: TABELLE (Treeview) ---
        tree_frame = tk.Frame(main_frame, bg=Style.BACKGROUND)
        tree_frame.grid(row=2, column=0, columnspan=2, sticky="nsew", pady=(5, 10))
        tree_frame.rowconfigure(0, weight=1)
        tree_frame.columnconfigure(0, weight=1)

        # Style für dunkle Tabelle
        style = ttk.Style()
        style.theme_use("default")
        style.configure("Treeview",
                        background="#222222",
                        foreground="white",
                        fieldbackground="#222222",
                        borderwidth=0,
                        rowheight=25)
        style.configure("Treeview.Heading",
                        background="#333333",
                        foreground="white",
                        font=("Arial", 10, "bold"),
                        borderwidth=1,
                        relief="flat")
        style.map("Treeview", background=[('selected', Style.ACCENT_PURPLE)])

        self.tree = ttk.Treeview(tree_frame, columns=('Command', 'Kosten'), show='headings', selectmode='browse')
        self.tree.heading('Command', text='Trigger (Text)')
        self.tree.heading('Kosten', text='Kosten')
        self.tree.column('Command', anchor='w', width=450)
        self.tree.column('Kosten', anchor='e', width=100)

        scrollbar = ttk.Scrollbar(tree_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)

        self.tree.grid(row=0, column=0, sticky="nsew")
        scrollbar.grid(row=0, column=1, sticky="ns")

        self.tree.bind('<<TreeviewSelect>>', self.on_item_select)

        main_frame.rowconfigure(2, weight=1)  # Tabelle füllt den Platz

        # --- SEKTION 3: EINGABE (CRUD) ---
        entry_frame = tk.Frame(main_frame, bg=Style.BACKGROUND)
        entry_frame.grid(row=3, column=0, columnspan=2, sticky="ew", pady=(10, 10))
        entry_frame.columnconfigure(0, weight=1)

        # Text
        tk.Label(entry_frame, text="Command Text:", **self.label_style).grid(row=0, column=0, sticky="w")
        self.entry_text_var = tk.StringVar()
        tk.Entry(entry_frame, textvariable=self.entry_text_var, **self.entry_style).grid(row=1, column=0, sticky="ew",
                                                                                         padx=(0, 10), ipady=3)

        # Kosten
        tk.Label(entry_frame, text="Kosten:", **self.label_style).grid(row=0, column=1, sticky="w")
        self.entry_costs_var = tk.StringVar()
        tk.Entry(entry_frame, textvariable=self.entry_costs_var, **self.entry_style, width=15).grid(row=1, column=1,
                                                                                                    sticky="w", ipady=3)

        # --- SEKTION 4: BUTTONS ---
        btn_frame = tk.Frame(main_frame, bg=Style.BACKGROUND)
        btn_frame.grid(row=4, column=0, columnspan=2, sticky="ew", pady=(10, 0))

        # Add Button (Grün)
        add_style = self.button_style.copy()
        add_style['bg'] = Style.SUCCESS
        tk.Button(btn_frame, text="HINZUFÜGEN", command=self.add_command, **add_style).pack(side=tk.LEFT, padx=(0, 5))

        # Edit Button
        self.edit_button = tk.Button(btn_frame, text="ÄNDERN", command=self.edit_command, **self.button_style,
                                     state="disabled")
        self.edit_button.pack(side=tk.LEFT, padx=5)

        # Delete Button (Rot)
        del_style = self.button_style.copy()
        del_style['bg'] = Style.DANGER
        self.delete_button = tk.Button(btn_frame, text="LÖSCHEN", command=self.delete_command, **del_style,
                                       state="disabled")
        self.delete_button.pack(side=tk.LEFT, padx=5)

        # Fire Button (Rechts, Blau)
        fire_style = self.button_style.copy()
        fire_style['bg'] = Style.ACCENT_BLUE
        tk.Button(btn_frame, text="▶ FIRE SEQUENZ", command=self.fire_command, **fire_style).pack(side=tk.RIGHT)

        # Initiale Daten laden
        self.load_commands()

    def save_duration_settings(self):
        try:
            duration = int(self.duration_var.get())
            if duration <= 0: raise ValueError
            self.service.save_settings({"display_duration_seconds": duration})
            show_toast(self, "Dauer gespeichert!")
        except:
            messagebox.showerror("Fehler", "Bitte eine gültige Zahl für die Dauer eingeben.")

    def load_commands(self):
        for item in self.tree.get_children():
            self.tree.delete(item)
        try:
            for cmd in self.service.get_all_commands():
                self.tree.insert('', 'end', iid=cmd['id'], values=(cmd.get('text', ''), cmd.get('costs', '')))
            self.clear_selection()
        except Exception as e:
            messagebox.showerror("Fehler", f"Ladefehler: {e}")

    def on_item_select(self, event):
        selected_items = self.tree.selection()
        if not selected_items: return

        self.selected_command_id = selected_items[0]
        item_values = self.tree.item(self.selected_command_id, 'values')

        if item_values:
            self.entry_text_var.set(item_values[0])
            self.entry_costs_var.set(item_values[1])
            self.edit_button.config(state="normal")
            self.delete_button.config(state="normal")

    def clear_selection(self):
        if self.tree.selection():
            self.tree.selection_remove(self.tree.selection())
        self.selected_command_id = None
        self.entry_text_var.set("")
        self.entry_costs_var.set("")
        self.edit_button.config(state="disabled")
        self.delete_button.config(state="disabled")

    def add_command(self):
        text = self.entry_text_var.get()
        costs = self.entry_costs_var.get()
        if not text or not costs:
            messagebox.showwarning("Fehler", "Text und Kosten dürfen nicht leer sein.")
            return
        try:
            self.service.add_command(text, costs)
            self.load_commands()
        except Exception as e:
            messagebox.showerror("Fehler", str(e))

    def edit_command(self):
        if not self.selected_command_id: return
        text = self.entry_text_var.get()
        costs = self.entry_costs_var.get()
        if not text or not costs: return
        try:
            self.service.update_command(self.selected_command_id, text, costs)
            self.load_commands()
        except Exception as e:
            messagebox.showerror("Fehler", str(e))

    def delete_command(self):
        if not self.selected_command_id: return
        if not messagebox.askyesno("Bestätigen", "Soll dieser Befehl wirklich gelöscht werden?"): return
        try:
            self.service.delete_command(self.selected_command_id)
            self.load_commands()
        except Exception as e:
            messagebox.showerror("Fehler", str(e))

    def fire_command(self):
        if not messagebox.askyesno("Bestätigen", "Soll die gesamte Command-Sequenz jetzt gestartet werden?"): return
        try:
            requests.post(BASE_URL.rstrip('/') + COMMANDS_TRIGGER_ENDPOINT, timeout=3)
            show_toast(self.master, "Command-Sequenz gestartet!")
        except Exception as e:
            messagebox.showerror("Fehler", f"Trigger Fehler: {e}")