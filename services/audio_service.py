import threading
import os
import time
import pygame
from config import get_path
from utils import server_log

class AudioService:
    def __init__(self):
        self.mixer_initialized = False
        try:
            pygame.mixer.init()
            self.mixer_initialized = True
            server_log.info("Pygame Mixer erfolgreich initialisiert.")
        except Exception as e:
            server_log.error(f"Pygame Mixer konnte nicht initialisiert werden: {e}")

    def _play_file_thread(self, relative_path):
        """Spielt eine spezifische Datei in einem Thread ab."""
        if not self.mixer_initialized:
            server_log.error("Mixer nicht initialisiert.")
            return

        full_path = get_path(relative_path)
        if not os.path.exists(full_path):
            server_log.error(f"Audiodatei nicht gefunden: {full_path}")
            return

        try:
            pygame.mixer.music.load(full_path)
            pygame.mixer.music.play()
            while pygame.mixer.music.get_busy():
                time.sleep(0.1)
        except Exception as e:
            server_log.error(f"Fehler beim Abspielen von {relative_path}: {e}")

    def play_goal_sound(self):
        """Spielt den Standard-Sound bei Erreichen eines Like-Ziels."""
        threading.Thread(target=self._play_file_thread, args=(os.path.join("assets", "sound.mp3"),), daemon=True).start()

    def play_end_sound(self):
        """Spielt den Paulchen Panther Sound am Ende des Subathons."""
        server_log.info("AudioService: Spiele Paulchen Panther Sound...")
        threading.Thread(target=self._play_file_thread, args=(os.path.join("assets", "paulchen_panther.mp3"),), daemon=True).start()