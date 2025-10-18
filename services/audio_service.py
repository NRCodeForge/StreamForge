import threading
import os
import time
import pygame  #
from config import get_path
from utils import server_log


class AudioService:
    """
    Ein Service zum Abspielen von Sounds mit Pygame,
    ohne den Flask-Server zu blockieren.
    """

    def __init__(self):
        self.sound_path = get_path(os.path.join("assets", "sound.mp3"))
        self.mixer_initialized = False

        if not os.path.exists(self.sound_path):
            server_log.warning(f"Audiodatei nicht gefunden: {self.sound_path}")
            self.sound_path = None

        try:
            # Initialisiere das Audio-Modul von Pygame
            pygame.mixer.init()
            self.mixer_initialized = True
            server_log.info("Pygame Mixer erfolgreich initialisiert.")
        except Exception as e:
            server_log.error(f"Pygame Mixer konnte nicht initialisiert werden: {e}")

    def _play_sound_thread(self):
        """Diese Funktion wird in einem separaten Thread ausgeführt."""
        if self.sound_path and self.mixer_initialized:
            try:
                # Lade den Sound
                pygame.mixer.music.load(self.sound_path)
                # Spiele den Sound ab
                pygame.mixer.music.play()

                # Warte im Thread, bis der Sound zu Ende gespielt wurde
                while pygame.mixer.music.get_busy():
                    time.sleep(0.1)

            except Exception as e:
                server_log.error(f"Fehler beim Abspielen von 'sound.mp3' mit Pygame: {e}")
        elif not self.sound_path:
            server_log.error("Sound konnte nicht abgespielt werden, da Pfad ungültig ist.")
        else:
            server_log.error("Sound konnte nicht abgespielt werden, da der Mixer nicht initialisiert wurde.")

    def play_goal_sound(self):
        """Startet das Abspielen des Sounds in einem neuen Thread."""
        server_log.info("AudioService: Spiele Ziel-Sound...")

        # Starte das Abspielen in einem Daemon-Thread,
        # damit es den Server nicht blockiert.
        thread = threading.Thread(target=self._play_sound_thread, daemon=True)
        thread.start()