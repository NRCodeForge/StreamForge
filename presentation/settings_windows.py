import tkinter as tk
from tkinter import messagebox, font
import sys

# KORREKTUR: Verwende absolute Importe
from services.like_challenge_service import LikeChallengeService
from services.subathon_service import SubathonService
from config import Style
from utils import server_log

# Globale Instanzen der Services
like_challenge_service = LikeChallengeService()
subathon_service = SubathonService()


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

        self.update_idletasks()
        w = self.winfo_width()
        h = self.winfo_height()
        x = master.winfo_x() + (master.winfo_width() // 2) - (w // 2)
        y = master.winfo_y() + (master.winfo_height() // 2) - (h // 2)
        self.geometry(f'+{x}+{y}')

        self.columnconfigure(0, weight=1)

        self.font_family = font.Font(family=Style.FONT_FAMILY, size=12)
        self.label_style = {"bg": Style.BACKGROUND, "fg": Style.FOREGROUND, "font": self.font_family}
        self.button_style = {"font": font.Font(family=Style.FONT_FAMILY, size=12, weight="bold"), "relief": tk.FLAT,
                             "bg": Style.ACCENT_PURPLE, "fg": Style.FOREGROUND, "activebackground": Style.WIDGET_HOVER}

        self.protocol("WM_DELETE_WINDOW", self.on_close)
        self.master = master

    def add_title(self, text):
        tk.Label(self, text=text, bg=Style.BACKGROUND, fg=Style.ACCENT_BLUE,
                 font=font.Font(family=Style.FONT_FAMILY, size=18, weight="bold")).pack(pady=(15, 10))

    def on_close(self):
        self.master.grab_release()
        self.destroy()


# --- Subathon Settings Window ---
class SubathonSettingsWindow(BaseSettingsWindow):
    def __init__(self, master):
        super().__init__(master, "Subathon Overlay Einstellungen", 500, 350)
        self.service = subathon_service
        self.add_title("Subathon Timer Einstellungen")

        self.current_settings = self.service.get_current_settings()

        main_frame = tk.Frame(self, bg=Style.BACKGROUND, padx=10, pady=10)
        main_frame.pack(fill='both', expand=True)

        tk.Label(main_frame, text="Timer Endzeit (ISO-Format):", **self.label_style).pack(pady=(10, 0))
        self.timer_end_entry = tk.Entry(main_frame, width=40, font=self.font_family)
        self.timer_end_entry.insert(0, self.current_settings.get("timer_end_timestamp", ""))
        self.timer_end_entry.pack(pady=5)

        tk.Button(main_frame, text="Einstellungen speichern", command=self.save_settings, **self.button_style).pack(
            pady=20)

    def save_settings(self):
        try:
            new_settings = self.current_settings.copy()
            new_settings["timer_end_timestamp"] = self.timer_end_entry.get()

            self.service.update_settings(new_settings)
            messagebox.showinfo(self.title(), "Subathon Einstellungen gespeichert!")
            self.on_close()
        except Exception as e:
            server_log.error(f"Subathon Speichern fehlgeschlagen: {e}")
            messagebox.showerror("Fehler", f"Speichern fehlgeschlagen: {e}")


# --- Like Challenge Settings Window ---
class LikeChallengeSettingsWindow(BaseSettingsWindow):
    def __init__(self, master):
        super().__init__(master, "Like Challenge Einstellungen", 600, 400)
        self.service = like_challenge_service
        self.add_title("Like Challenge Ziel-Konfiguration")

        try:
            # Muss über den SettingsManager im Service direkt die Datei laden
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
            entry = tk.Entry(form_frame, width=50, font=self.font_family)
            entry.insert(0, self.current_settings.get(key, ""))
            entry.grid(row=row, column=1, sticky="ew", pady=5, padx=5)
            self.entries[key] = entry

        tk.Label(form_frame, text="Initiale Ziele (kommasepariert):", **self.label_style).grid(row=3, column=0,
                                                                                               sticky="w", pady=5,
                                                                                               padx=5)
        initial_goals_str = ", ".join(map(str, self.current_settings.get("initialGoals", [])))
        self.goals_entry = tk.Entry(form_frame, width=50, font=self.font_family)
        self.goals_entry.insert(0, initial_goals_str)
        self.goals_entry.grid(row=3, column=1, sticky="ew", pady=5, padx=5)

        tk.Button(self, text="Einstellungen speichern", command=self.save_settings, **self.button_style).pack(pady=20)

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
            server_log.error(f"Like Challenge Speichern fehlgeschlagen: {e}")
            messagebox.showerror("Fehler", f"Speichern fehlgeschlagen: {e}")