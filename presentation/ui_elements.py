import tkinter as tk
from tkinter import messagebox, font
import requests
import threading
from pynput import keyboard
import sys

# KORREKTUR: Verwende absolute Imports
from config import Style, BASE_URL, NEXT_WISH_ENDPOINT, RESET_WISHES_ENDPOINT
from utils import server_log


# --- Hotkey-Listener-Funktion ---
def start_hotkey_listener(is_server_running_ref):
    """Startet einen Thread zum Abhören des Hotkeys 'Bild Runter' für den nächsten Wunsch."""

    def on_press(key):
        try:
            # Prüft, ob der Server läuft UND die richtige Taste gedrückt wurde
            if key == keyboard.Key.page_down and is_server_running_ref[0]:
                # Sendet die Anfrage an den Server
                requests.post(BASE_URL.rstrip('/') + NEXT_WISH_ENDPOINT, timeout=1)
                server_log.info("Hotkey 'Bild Runter' ausgelöst: Nächster Wunsch angefordert.")
        except requests.exceptions.RequestException:
             # Ignoriert Fehler, wenn der Server nicht erreichbar ist
            pass
        except Exception as e:
            server_log.error(f"Unerwarteter Hotkey-Fehler: {e}")

    # Stellt sicher, dass der Listener im Hintergrund läuft (daemon=True)
    # keyboard.Listener(...).start() blockiert normalerweise, daher der Thread.
    listener_thread = threading.Thread(target=lambda: keyboard.Listener(on_press=on_press).start(), daemon=True)
    listener_thread.start()
    # WICHTIG: .join() hier *nicht* aufrufen, sonst blockiert die GUI!
    # Der Listener läuft jetzt im Hintergrund, bis das Hauptprogramm endet.
    server_log.info("Hotkey-Listener-Thread gestartet.") # Log hinzugefügt
    return listener_thread # Rückgabe ist optional, wird aktuell nicht verwendet


# --- Toast Notification ---
def show_toast(root, message, color=Style.SUCCESS):
    """Zeigt eine nicht-blockierende Toast-Benachrichtigung an."""
    toast = tk.Toplevel(root)
    toast.wm_overrideredirect(True)
    toast.config(bg=color, padx=10, pady=5)
    label = tk.Label(toast, text=message, font=font.Font(family=Style.FONT_FAMILY, size=10, weight="bold"),
                     bg=color, fg="#FFFFFF")
    label.pack()

    root.update_idletasks()
    root_x = root.winfo_x()
    root_y = root.winfo_y()
    root_width = root.winfo_width()
    toast_width = toast.winfo_width()
    x = root_x + root_width - toast_width - 20
    y = root_y + 20

    toast.geometry(f'+{x}+{y}')
    toast.attributes("-topmost", True)
    root.after(3000, toast.destroy)


# --- UIElementCard ---
class UIElementCard(tk.Frame):
    """Eine wiederverwendbare Karte für jedes Overlay-Element."""

    def __init__(self, parent, name, path, has_settings=False, has_reset=False, settings_func=None, reset_func=None):

        super().__init__(parent, bg=Style.WIDGET_BG, padx=20, pady=15, highlightbackground=Style.BORDER,
                         highlightthickness=1, cursor="hand2")

        self.root = parent.winfo_toplevel()
        # BASE_URL ist jetzt über den absoluten Import verfügbar
        self.url = BASE_URL.rstrip('/') + '/' + path.lstrip('/')

        self.button_style = {
            "font": font.Font(family=Style.FONT_FAMILY, size=12),
            "relief": tk.FLAT,
            "borderwidth": 0,
            "bg": Style.WIDGET_BG,
            "activebackground": Style.WIDGET_HOVER
        }

        self.columnconfigure(0, weight=1)
        self.columnconfigure(1, weight=0)
        self.columnconfigure(2, weight=0)
        self.columnconfigure(3, weight=0)

        # Name Label
        self.name_label = tk.Label(self, text=name,
                                   font=font.Font(family=Style.FONT_FAMILY, size=16, weight="bold"),
                                   bg=Style.WIDGET_BG, fg=Style.FOREGROUND)
        self.name_label.grid(row=0, column=0, sticky="w")

        # Copy Button
        self.copy_button = tk.Button(self, text="📋", fg=Style.ACCENT_BLUE, **self.button_style,
                                     command=self._on_copy_click)
        self.copy_button.grid(row=0, column=3, sticky="e", padx=(5, 0))

        # KORRIGIERTE LOGIK: Erstellt Button nur, wenn die Funktion vorhanden ist (nicht None).
        if reset_func:
            self.reset_button = tk.Button(self, text="🗑️", fg=Style.DANGER, **self.button_style, command=reset_func)
            self.reset_button.grid(row=0, column=1, sticky="e", padx=(10, 0))
            self._bind_hover_color(self.reset_button, Style.DANGER, Style.DANGER)

        # KORRIGIERTE LOGIK: Erstellt Button nur, wenn die Funktion vorhanden ist (nicht None).
        if settings_func:
            self.settings_button = tk.Button(self, text="⚙️", fg=Style.TEXT_MUTED, **self.button_style,
                                             command=settings_func)
            self.settings_button.grid(row=0, column=2, sticky="e", padx=(5, 0))
            self._bind_hover_color(self.settings_button, Style.ACCENT_PURPLE, Style.TEXT_MUTED)

        self._bind_hover_effect_to_all()
        self._bind_hover_color(self.copy_button, Style.ACCENT_BLUE, Style.ACCENT_BLUE)

    def _on_enter(self, event):
        """Mouse-Over-Effekt: hebt die Karte und ihre Kinder farblich hervor."""
        self.config(bg=Style.WIDGET_HOVER)
        for widget in self.winfo_children():
            widget.config(bg=Style.WIDGET_HOVER)

    def _on_leave(self, event):
        """Mouse-Out-Effekt: stellt die Standardfarben wieder her."""
        self.config(bg=Style.WIDGET_BG)
        for widget in self.winfo_children():
            if widget not in [getattr(self, 'reset_button', None), getattr(self, 'settings_button', None),
                              self.copy_button]:
                widget.config(bg=Style.WIDGET_BG)

    def _bind_hover_color(self, widget, enter_fg, leave_fg):
        """Bindet nur die Farbänderung für den Text eines Buttons an Hover-Events."""
        widget.bind("<Enter>", lambda e, w=widget, c=enter_fg: w.config(fg=c), add='+')
        widget.bind("<Leave>", lambda e, w=widget, c=leave_fg: w.config(fg=c), add='+')

    def _bind_hover_effect_to_all(self):
        """Bindet die allgemeinen Hover-In/Out-Events an die Karte und alle direkten Kinder."""
        widgets = [self] + self.winfo_children()
        for widget in widgets:
            widget.bind("<Enter>", self._on_enter)
            widget.bind("<Leave>", self._on_leave)

    def _on_copy_click(self):
        """Kopiert die URL des Overlays in die Zwischenablage und zeigt einen Toast an."""
        self.root.clipboard_clear()
        self.root.clipboard_append(self.url)
        show_toast(self.root, "In Zwischenablage kopiert")