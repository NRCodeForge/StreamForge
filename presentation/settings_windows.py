import tkinter as tk
from tkinter import messagebox, font
import requests
import sys

# Importiere Service Layer
from services.service_provider import (
    like_service_instance,
    subathon_service_instance
)

# Importiere Infrastruktur
from config import Style


# --- Allgemeine Basisklasse für Einstellungsfenster ---
class BaseSettingsWindow(tk.Toplevel):
    def __init__(self, master, title, width=550, height=450):
        super().__init__(master)
        self.title(title)
        self.geometry(f"{width}x{height}")
        self.transient(master)  # Sorgt dafür, dass das Fenster über dem Master-Fenster bleibt
        self.grab_set()  # Blockiert Interaktion mit dem Hauptfenster
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
        # Gibt die Interaktion an das Hauptfenster zurück
        self.master.grab_release()


# --- Subathon Settings Window (KOMPLETT ERSETZT) ---
class SubathonSettingsWindow(BaseSettingsWindow):
    def __init__(self, master):
        # Neue Fenstergröße, passend zum Design
        super().__init__(master, "Subathon Timer Einstellungen", 550, 550)

        self.service = subathon_service_instance
        self.add_title("Subathon Timer Konfiguration")

        try:
            self.current_settings = self.service.get_current_settings()
        except Exception as e:
            messagebox.showerror("Fehler", f"Fehler beim Laden der Subathon-Einstellungen: {e}")
            self.on_close()
            return

        # Container für die Widgets, um sie später auszulesen
        self.widgets = {}

        # --- Haupt-Frame für den Inhalt ---
        main_frame = tk.Frame(self, bg=Style.BACKGROUND, padx=20)
        main_frame.pack(fill='both', expand=True)

        # --- Sektion: Allgemein ---
        self.add_section_title("Allgemein", main_frame)

        anim_frame = tk.Frame(main_frame, bg=Style.BACKGROUND)
        anim_frame.pack(fill='x', pady=5)
        tk.Label(anim_frame, text="Animationsdauer (Sekunden):", **self.label_style, width=25, anchor="w").pack(
            side=tk.LEFT)

        anim_entry = tk.Entry(anim_frame, **self.entry_style)
        anim_entry.insert(0, self.current_settings.get("animations_time", "3"))
        anim_entry.pack(side=tk.LEFT, fill='x', expand=True, padx=5)
        self.widgets["animations_time"] = anim_entry

        # --- Sektion: Event-Dauer und Status ---
        self.add_section_title("Event-Dauer und Status", main_frame)

        # Definiert die Reihenfolge und die Anzeigetexte
        self.event_keys = [
            ("coins", "Coins:"),
            ("subscribe", "Subscribe:"),
            ("follow", "Follow:"),
            ("share", "Share:"),
            ("like", "Like:"),
            ("chat", "Chat:")
        ]

        # Erstelle die UI-Elemente für jedes Event
        for key, display_text in self.event_keys:
            event_data = self.current_settings.get(key, {"value": "0 Seconds", "active": False})

            row_frame = tk.Frame(main_frame, bg=Style.BACKGROUND)
            row_frame.pack(fill='x', pady=5)

            # Label (z.B. "Coins:")
            tk.Label(row_frame, text=display_text, **self.label_style, width=15, anchor="w").pack(side=tk.LEFT)

            # Entry-Feld (z.B. "3 Seconds")
            entry = tk.Entry(row_frame, **self.entry_style)
            entry.insert(0, event_data.get("value"))
            entry.pack(side=tk.LEFT, fill='x', expand=True, padx=5)

            # Checkbox-Variable (True/False)
            var = tk.BooleanVar(value=event_data.get("active"))

            # Checkbox (z.B. "Aktiv")
            chk = tk.Checkbutton(row_frame, text="Aktiv", variable=var, **self.check_style)
            chk.pack(side=tk.RIGHT, padx=5)

            # Speichere die Widgets für den Save-Vorgang
            self.widgets[key] = {"value_entry": entry, "active_var": var}

        # --- Speichern Button ---
        tk.Button(main_frame, text="Speichern & Schließen", command=self.save_settings, **self.button_style).pack(
            pady=30, fill='x')

    def save_settings(self):
        try:
            new_settings = {}

            # Speichere "Allgemein"
            new_settings["animations_time"] = self.widgets["animations_time"].get()

            # Speichere "Events"
            for key, _ in self.event_keys:
                widgets = self.widgets[key]
                new_settings[key] = {
                    "value": widgets["value_entry"].get(),
                    "active": widgets["active_var"].get()
                }

            # Rufe den Service auf, um die JSON zu schreiben
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
        self.add_title("Like Challenge Ziel-Konfiguration", color=Style.ACCENT_PURPLE)  # Kleine Design-Anpassung

        # Läd die Einstellungen direkt über den Manager des Service
        try:
            self.current_settings = self.service.settings_manager.load_settings()
        except Exception:
            # Falls Datei fehlt oder korrupt, leeren Standard verwenden
            self.current_settings = {"widgetUrl": "", "displayTextFormat": "{likes_needed} Likes",
                                     "recurringGoalExpression": "x + 33333", "initialGoals": []}

        form_frame = tk.Frame(self, bg=Style.BACKGROUND, padx=20)
        form_frame.pack(pady=10, fill='x')
        form_frame.columnconfigure(1, weight=1)

        # --- Felder ---
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

        # Initial Goals (spezielles Feld)
        tk.Label(form_frame, text="Initiale Ziele (kommasepariert):", **self.label_style).grid(row=3, column=0,
                                                                                               sticky="w", pady=5,
                                                                                               padx=5)
        initial_goals_str = ", ".join(map(str, self.current_settings.get("initialGoals", [])))
        self.goals_entry = tk.Entry(form_frame, **self.entry_style, width=50)
        self.goals_entry.insert(0, initial_goals_str)
        self.goals_entry.grid(row=3, column=1, sticky="ew", pady=5, padx=5)

        # Speichern Button
        tk.Button(self, text="Einstellungen speichern", command=self.save_settings, **self.button_style).pack(pady=20,
                                                                                                              fill='x',
                                                                                                              padx=20)

    def save_settings(self):
        try:
            # Versuche, die Ziele zu parsen
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