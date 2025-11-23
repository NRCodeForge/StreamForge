import tkinter as tk
from tkinter import messagebox, font, ttk
import requests
import sys

# Importiere Service Layer
from services.service_provider import (
    like_service_instance,
    subathon_service_instance,
    command_service_instance  # NEU
)

# Importiere Infrastruktur
# (Wir brauchen hier keine API-Endpunkte mehr, da der Trigger extern ist)
from config import Style, BASE_URL, COMMANDS_TRIGGER_ENDPOINT
from presentation.ui_elements import show_toast  # Importiert für den Speicher-Button
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
                            "font": font.Font(family=Style.FONT_FAMILY, size=12)}
        self.entry_style = {"font": font.Font(family=Style.FONT_FAMILY, size=11)}
        self.check_style = {"bg": Style.BACKGROUND, "fg": Style.FOREGROUND, "selectcolor": Style.WIDGET_BG,
                            "activebackground": Style.BACKGROUND, "activeforeground": Style.FOREGROUND,
                            "font": font.Font(family=Style.FONT_FAMILY, size=11)}
        self.button_style = {"font": font.Font(family=Style.FONT_FAMILY, size=12, weight="bold"), "relief": tk.FLAT,
                             "bg": Style.ACCENT_PURPLE, "fg": Style.FOREGROUND, "activebackground": Style.WIDGET_HOVER,
                             "pady": 5}

        self.protocol("WM_DELETE_WINDOW", self.on_close)
        self.master = master

    def add_title(self, text, color=Style.ACCENT_BLUE):
        tk.Label(self, text=text, bg=Style.BACKGROUND, fg=color,
                 font=font.Font(family=Style.FONT_FAMILY, size=18, weight="bold")).pack(pady=(15, 10))

    def add_section_title(self, text, frame):
        tk.Label(frame, text=text, bg=Style.BACKGROUND, fg=Style.ACCENT_BLUE,
                 font=font.Font(family=Style.FONT_FAMILY, size=14, weight="bold")).pack(pady=(10, 5), anchor="w")

    def on_close(self):
        self.destroy()
        self.master.grab_release()


# --- Subathon Settings Window (KOMPLETT ERSETZT) ---
class SubathonSettingsWindow(BaseSettingsWindow):
    def __init__(self, master):
        super().__init__(master, "Subathon Timer Einstellungen", 550, 550)
        self.service = subathon_service_instance
        self.add_title("Subathon Timer Konfiguration")
        try:
            self.current_settings = self.service.get_current_settings()
        except Exception as e:
            messagebox.showerror("Fehler", f"Fehler beim Laden der Subathon-Einstellungen: {e}")
            self.on_close()
            return
        self.widgets = {}
        main_frame = tk.Frame(self, bg=Style.BACKGROUND, padx=20)
        main_frame.pack(fill='both', expand=True)
        self.add_section_title("Allgemein", main_frame)
        anim_frame = tk.Frame(main_frame, bg=Style.BACKGROUND)
        anim_frame.pack(fill='x', pady=5)
        tk.Label(anim_frame, text="Animationsdauer (Sekunden):", **self.label_style, width=25, anchor="w").pack(
            side=tk.LEFT)
        anim_entry = tk.Entry(anim_frame, **self.entry_style)
        anim_entry.insert(0, self.current_settings.get("animations_time", "3"))
        anim_entry.pack(side=tk.LEFT, fill='x', expand=True, padx=5)
        self.widgets["animations_time"] = anim_entry
        self.add_section_title("Event-Dauer und Status", main_frame)
        self.event_keys = [
            ("coins", "Coins:"),
            ("subscribe", "Subscribe:"),
            ("follow", "Follow:"),
            ("share", "Share:"),
            ("like", "Like:"),
            ("chat", "Chat:")
        ]
        for key, display_text in self.event_keys:
            event_data = self.current_settings.get(key, {"value": "0 Seconds", "active": False})
            row_frame = tk.Frame(main_frame, bg=Style.BACKGROUND)
            row_frame.pack(fill='x', pady=5)
            tk.Label(row_frame, text=display_text, **self.label_style, width=15, anchor="w").pack(side=tk.LEFT)
            entry = tk.Entry(row_frame, **self.entry_style)
            entry.insert(0, event_data.get("value"))
            entry.pack(side=tk.LEFT, fill='x', expand=True, padx=5)
            var = tk.BooleanVar(value=event_data.get("active"))
            chk = tk.Checkbutton(row_frame, text="Aktiv", variable=var, **self.check_style)
            chk.pack(side=tk.RIGHT, padx=5)
            self.widgets[key] = {"value_entry": entry, "active_var": var}
        tk.Button(main_frame, text="Speichern & Schließen", command=self.save_settings, **self.button_style).pack(
            pady=30, fill='x')

    def save_settings(self):
        try:
            new_settings = {}
            new_settings["animations_time"] = self.widgets["animations_time"].get()
            for key, _ in self.event_keys:
                widgets = self.widgets[key]
                new_settings[key] = {
                    "value": widgets["value_entry"].get(),
                    "active": widgets["active_var"].get()
                }
            self.service.update_settings(new_settings)
            messagebox.showinfo(self.title(), "Subathon Einstellungen gespeichert!")
            self.on_close()
        except Exception as e:
            messagebox.showerror("Fehler", f"Speichern fehlgeschlagen: {e}")


# --- Like Challenge Settings Window (UNVERÄNDERT) ---
class LikeChallengeSettingsWindow(BaseSettingsWindow):
    def __init__(self, master):
        super().__init__(master, "Like Challenge Einstellungen", 600, 400)
        self.service = like_service_instance
        self.add_title("Like Challenge Ziel-Konfiguration", color=Style.ACCENT_PURPLE)
        try:
            self.current_settings = self.service.settings_manager.load_settings()
        except Exception:
            self.current_settings = {"widgetUrl": "", "displayTextFormat": "{likes_needed} Likes",
                                     "recurringGoalExpression": "x + 33333", "initialGoals": []}
        form_frame = tk.Frame(self, bg=Style.BACKGROUND, padx=20)
        form_frame.pack(pady=10, fill='x')
        form_frame.columnconfigure(1, weight=1)
        fields = [
            ("Tikfinity Widget URL:", "widgetUrl", 0),
            ("Anzeigeformat ({likes_needed}):", "displayTextFormat", 1),
            ("Rekursive Zielformel (mit 'x'):", "recurringGoalExpression", 2),
        ]
        self.entries = {}
        for i, (label_text, key, row) in enumerate(fields):
            tk.Label(form_frame, text=label_text, **self.label_style).grid(row=row, column=0, sticky="w", pady=5,
                                                                           padx=5)
            entry = tk.Entry(form_frame, **self.entry_style, width=50)
            entry.insert(0, self.current_settings.get(key, ""))
            entry.grid(row=row, column=1, sticky="ew", pady=5, padx=5)
            self.entries[key] = entry
        tk.Label(form_frame, text="Initiale Ziele (kommasepariert):", **self.label_style).grid(row=3, column=0,
                                                                                               sticky="w", pady=5,
                                                                                               padx=5)
        initial_goals_str = ", ".join(map(str, self.current_settings.get("initialGoals", [])))
        self.goals_entry = tk.Entry(form_frame, **self.entry_style, width=50)
        self.goals_entry.insert(0, initial_goals_str)
        self.goals_entry.grid(row=3, column=1, sticky="ew", pady=5, padx=5)
        tk.Button(self, text="Einstellungen speichern", command=self.save_settings, **self.button_style).pack(pady=20,
                                                                                                              fill='x',
                                                                                                              padx=20)

    def save_settings(self):
        try:
            raw_goals = self.goals_entry.get().split(',')
            initial_goals = sorted([int(g.strip()) for g in raw_goals if g.strip()])
            new_settings = {
                "widgetUrl": self.entries["widgetUrl"].get(),
                "displayTextFormat": self.entries["displayTextFormat"].get(),
                "recurringGoalExpression": self.entries["recurringGoalExpression"].get(),
                "initialGoals": initial_goals
            }
            self.service.settings_manager.save_settings(new_settings)
            messagebox.showinfo(self.title(), "Like Challenge Einstellungen gespeichert!")
            self.on_close()
        except ValueError:
            messagebox.showerror("Fehler", "Initiale Ziele müssen Ganzzahlen sein und korrekt formatiert.")
        except Exception as e:
            messagebox.showerror("Fehler", f"Speichern fehlgeschlagen: {e}")


# --- Commands Settings Window (MODIFIZIERT) ---
class CommandsSettingsWindow(BaseSettingsWindow):
    def __init__(self, master):
        super().__init__(master, "Command Overlay Einstellungen", 700, 600)  # Höhe angepasst

        self.service = command_service_instance
        self.add_title("Command Overlay Konfiguration")

        self.selected_command_id = None

        # --- Haupt-Frame ---
        main_frame = tk.Frame(self, bg=Style.BACKGROUND, padx=15, pady=10)
        main_frame.pack(fill='both', expand=True)
        main_frame.columnconfigure(0, weight=1)  # Spalte 0 (links)
        main_frame.columnconfigure(1, weight=1)  # Spalte 1 (rechts)

        # --- Sektion 1: Anzeigedauer (NEU) ---
        settings_frame = tk.Frame(main_frame, bg=Style.BACKGROUND)
        settings_frame.grid(row=0, column=0, columnspan=2, sticky="ew", pady=(0, 15))  # Über beide Spalten

        tk.Label(settings_frame, text="Anzeigedauer pro Command (Sek.):", **self.label_style).pack(side=tk.LEFT,
                                                                                                   padx=(0, 10))

        try:
            self.settings = self.service.get_settings()
        except Exception as e:
            server_log.error(f"Fehler beim Laden der Command-Settings: {e}")
            self.settings = {"display_duration_seconds": 5}  # Fallback

        self.duration_var = tk.StringVar(value=self.settings.get("display_duration_seconds", 5))
        self.duration_entry = tk.Entry(settings_frame, textvariable=self.duration_var, **self.entry_style, width=10)
        self.duration_entry.pack(side=tk.LEFT)

        duration_save_button = tk.Button(settings_frame, text="Dauer speichern", command=self.save_duration_settings,
                                         **self.button_style)
        duration_save_button.pack(side=tk.LEFT, padx=(10, 0))

        # Trennlinie
        separator = tk.Frame(main_frame, height=1, bg=Style.BORDER)
        separator.grid(row=1, column=0, columnspan=2, sticky="ew", pady=(10, 15))

        # --- Sektion 2: Befehlsliste (Tabelle) ---
        tree_frame = tk.Frame(main_frame, bg=Style.BACKGROUND)
        tree_frame.grid(row=2, column=0, columnspan=2, sticky="nsew", pady=(5, 10))  # Über beide Spalten
        tree_frame.rowconfigure(0, weight=1)
        tree_frame.columnconfigure(0, weight=1)

        # Style für Treeview
        style = ttk.Style()
        style.theme_use("default")
        style.configure("Treeview", background=Style.WIDGET_BG, foreground=Style.FOREGROUND,
                        fieldbackground=Style.WIDGET_BG, borderwidth=0, rowheight=25)
        style.configure("Treeview.Heading", background=Style.BACKGROUND, foreground=Style.ACCENT_BLUE,
                        font=font.Font(family=Style.FONT_FAMILY, size=11, weight="bold"), borderwidth=0)
        style.map("Treeview", background=[('selected', Style.ACCENT_PURPLE)])
        style.map("Treeview.Heading", background=[('active', Style.WIDGET_HOVER)])

        self.tree = ttk.Treeview(tree_frame, columns=('Command', 'Kosten'), show='headings', selectmode='browse')
        self.tree.heading('Command', text='Command Text')
        self.tree.heading('Kosten', text='Kosten (Whieties)')
        self.tree.column('Command', anchor='w', width=400)
        self.tree.column('Kosten', anchor='e', width=150)

        scrollbar = ttk.Scrollbar(tree_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)

        self.tree.grid(row=0, column=0, sticky="nsew")
        scrollbar.grid(row=0, column=1, sticky="ns")

        self.tree.bind('<<TreeviewSelect>>', self.on_item_select)

        main_frame.rowconfigure(2, weight=1)  # Tabelle füllt den Platz

        # --- Sektion 3: Eingabefelder (CRUD) ---
        entry_frame = tk.Frame(main_frame, bg=Style.BACKGROUND)
        entry_frame.grid(row=3, column=0, columnspan=2, sticky="ew", pady=(5, 10))  # Über beide Spalten
        entry_frame.columnconfigure(0, weight=1)

        tk.Label(entry_frame, text="Command Text:", **self.label_style).grid(row=0, column=0, sticky="w")
        self.entry_text_var = tk.StringVar()
        self.entry_text_field = tk.Entry(entry_frame, textvariable=self.entry_text_var, **self.entry_style)
        self.entry_text_field.grid(row=1, column=0, sticky="ew", padx=(0, 10))

        tk.Label(entry_frame, text="Kosten (Whieties):", **self.label_style).grid(row=0, column=1, sticky="w")
        self.entry_costs_var = tk.StringVar()
        self.entry_costs_field = tk.Entry(entry_frame, textvariable=self.entry_costs_var, **self.entry_style, width=20)
        self.entry_costs_field.grid(row=1, column=1, sticky="w")

        # --- Sektion 4: CRUD-Buttons (Links) ---
        button_frame = tk.Frame(main_frame, bg=Style.BACKGROUND)
        button_frame.grid(row=4, column=0, sticky="w", pady=(10, 0))  # Spalte 0

        # (MIT TYPEERROR FIX)
        add_button_style = self.button_style.copy()
        add_button_style['bg'] = Style.SUCCESS
        self.add_button = tk.Button(button_frame, text="Hinzufügen", command=self.add_command, **add_button_style)
        self.add_button.pack(side=tk.LEFT, padx=(0, 5))

        self.edit_button = tk.Button(button_frame, text="Ändern", command=self.edit_command, **self.button_style,
                                     state="disabled")
        self.edit_button.pack(side=tk.LEFT, padx=5)

        delete_button_style = self.button_style.copy()
        delete_button_style['bg'] = Style.DANGER
        self.delete_button = tk.Button(button_frame, text="Löschen", command=self.delete_command, **delete_button_style,
                                       state="disabled")
        self.delete_button.pack(side=tk.LEFT, padx=5)

        # --- Sektion 5: Fire Button (Rechts) ---
        fire_frame = tk.Frame(main_frame, bg=Style.BACKGROUND)
        fire_frame.grid(row=4, column=1, sticky="e", pady=(10, 0))  # Spalte 1

        fire_button_style = self.button_style.copy()
        fire_button_style['bg'] = Style.ACCENT_BLUE
        fire_button_style['font'] = font.Font(family=Style.FONT_FAMILY, size=14, weight="bold")
        fire_button_style['pady'] = 10

        self.fire_button = tk.Button(fire_frame, text="🔥 SEQUENZ STARTEN", command=self.fire_command,
                                     **fire_button_style)
        self.fire_button.pack()

        # Lade die initialen Daten für die Tabelle
        self.load_commands()

    def save_duration_settings(self):
        """Speichert nur die Anzeigedauer."""
        try:
            duration = int(self.duration_var.get())
            if duration <= 0:
                raise ValueError("Dauer muss positiv sein.")
            self.service.save_settings({"display_duration_seconds": duration})
            show_toast(self, "Anzeigedauer gespeichert!")
        except ValueError:
            messagebox.showerror("Fehler", "Bitte eine gültige Zahl (z.B. 5) für die Dauer eingeben.")
        except Exception as e:
            messagebox.showerror("Fehler", f"Fehler beim Speichern der Dauer: {e}")

    def load_commands(self):
        """Lädt alle Befehle (aus commands.json) und füllt die Tabelle."""
        for item in self.tree.get_children():
            self.tree.delete(item)
        try:
            commands = self.service.get_all_commands()
            for cmd in commands:
                self.tree.insert('', 'end', iid=cmd['id'], values=(cmd.get('text', ''), cmd.get('costs', '')))
            self.clear_selection()
        except Exception as e:
            messagebox.showerror("Fehler", f"Befehle konnten nicht geladen werden: {e}")

    def on_item_select(self, event):
        selected_items = self.tree.selection()
        if not selected_items:
            return
        self.selected_command_id = selected_items[0]
        item_values = self.tree.item(self.selected_command_id, 'values')
        if item_values and len(item_values) >= 2:
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
            messagebox.showerror("Fehler", f"Fehler beim Hinzufügen: {e}")

    def edit_command(self):
        if not self.selected_command_id:
            return
        new_text = self.entry_text_var.get()
        new_costs = self.entry_costs_var.get()
        if not new_text or not new_costs:
            messagebox.showwarning("Fehler", "Text und Kosten dürfen nicht leer sein.")
            return
        try:
            self.service.update_command(self.selected_command_id, new_text, new_costs)
            self.load_commands()
        except Exception as e:
            messagebox.showerror("Fehler", f"Fehler beim Ändern: {e}")

    def delete_command(self):
        if not self.selected_command_id:
            return
        if not messagebox.askyesno("Bestätigen", "Soll dieser Befehl wirklich gelöscht werden?"):
            return
        try:
            self.service.delete_command(self.selected_command_id)
            self.load_commands()
        except Exception as e:
            messagebox.showerror("Fehler", f"Fehler beim Löschen: {e}")

    def fire_command(self):
        """Triggert die Webhook (genau wie Tikfinity)."""
        if not messagebox.askyesno("Bestätigen", "Soll die gesamte Command-Sequenz jetzt gestartet werden?"):
            return
        try:
            # Mache einen POST Request an den Trigger Endpunkt
            response = requests.post(BASE_URL.rstrip('/') + COMMANDS_TRIGGER_ENDPOINT, timeout=3)
            response.raise_for_status()
            show_toast(self.master, "Command-Sequenz gestartet!")  # Toast auf Hauptfenster
        except requests.exceptions.RequestException as e:
            messagebox.showerror("Fehler", f"Serverfehler beim Triggern: {e}")