# StreamForge 

**StreamForge** ist ein hochflexibler Desktop-Manager für Stream-Overlays mit einer integrierten lokalen Web-API. Die Anwendung ermöglicht es Streamern, interaktive Overlays wie Wunschlisten, Subathons, Glücksräder und Like-Challenges direkt über eine benutzerfreundliche Tkinter-GUI zu verwalten und in Echtzeit zu steuern.

---

##  Projekt-Hintergrund & Portfolio
Dieses Projekt wurde im Auftrag des Streamers **WhieteRedi** entwickelt. Es handelt sich um ein **unentgeltliches Portfolio-Projekt**, das die Integration moderner Web-Technologien (Flask, Playwright) in eine klassische Desktop-Umgebung (Python, Tkinter) demonstriert.

- **Auftraggeber:** [WhieteRedi](https://www.twitch.tv/whieteredi)
- **Status:** Portfolio-Projekt / Open Source
- **Vergütung:** Keine (unentgeltlicher Ausgleich)

---

##  Hauptfunktionen & Module

StreamForge bietet eine Vielzahl an Modulen, die über dedizierte Services gesteuert werden:

* **Wishlist (Killer Wishes):** Zuschauer können Wünsche einreichen, die in einer SQLite-Datenbank gespeichert und nacheinander im Overlay angezeigt werden.
* **Like Challenge:** Echtzeit-Tracking von TikTok-Likes über eine automatisierte Playwright-Instanz.
* **Subathon & Timer:** Ein dynamisches System zur Verwaltung von Marathon-Streams mit automatischen Zeitgutschriften.
* **Wheel of Fortune:** Ein interaktives Glücksrad, das über den Chat oder die GUI ausgelöst werden kann.
* **Gambler & Loot:** Mini-Games für den Stream-Chat zur Steigerung der Zuschauerbindung.
* **Command System:** Eigene Chat-Befehle mit Sound-Trigger-Funktion und Cooldown-Management.
* **Currency Service:** Verwaltung einer lokalen Stream-Währung für Interaktionen.
* **Audio-Engine:** Ein hybrides System zur Wiedergabe von Sounds bei bestimmten Events wie Follows oder Goals.

---

## API-Referenz (v1)

Die lokale API ist unter `http://127.0.0.1:5000` erreichbar und ermöglicht die Kommunikation zwischen den Overlays und dem Python-Backend.

### Endpunkte
* **Wunschliste:**
    * `GET /api/v1/wishes` – Ruft die aktuellen Wünsche ab.
    * `POST /api/v1/wishes` – Fügt einen neuen Wunsch hinzu.
    * `POST /api/v1/wishes/next` – Springt zum nächsten Wunsch.
    * `POST /api/v1/wishes/reset` – Löscht alle Wünsche.
* **Like-Challenge:**
    * `GET /api/v1/like_challenge` – Gibt den aktuellen Fortschritt zurück.
    * `POST /api/v1/like_challenge/update` – Manuelles Update der Like-Zahlen.
* **Subathon:**
    * `GET /api/v1/subathon` – Status des Subathon-Timers.
    * `POST /api/v1/subathon/add_time` – Fügt dem Timer manuell Zeit hinzu.

### Statische Overlays (Browser-Quellen für OBS)
* `/killer_wishes/` – Overlay für die Wunschliste.
* `/subathon_overlay/` – Anzeige für den Subathon.
* `/timer_overlay/` – Allgemeiner Countdown-Timer.
* `/like_overlay/` – Visualisierung der Like-Challenge.
* `/wheel_overlay/` – Das interaktive Glücksrad.
* `/commands_overlay/` – Visualisierung von Chat-Befehlen.
* `/gambler_overlay/` – UI für die Mini-Games.
* `/loot_overlay/` – Loot-Benachrichtigungen.
* `/place_overlay/` – Spezielles Place-Event Overlay.

---

##  Wichtiger Hinweis zu Mediendateien
Aus Speicherplatzgründen sind bestimmte Mediendateien im Repository **nicht enthalten** und müssen manuell hinzugefügt werden:

**Fehlende Audio-Dateien (`assets/`):**
- `assets/paulchen_panther.mp3`
- `assets/sound.mp3`

**Fehlende Video-Dateien (`assets/videos/`):**
- `assets/videos/superfan.mp4`
- `assets/videos/treasure.mp4`

---

##  Tech-Stack
* **Backend:** Python 3.10+ mit Flask
* **GUI:** Tkinter & Pillow (PIL)
* **Automatisierung:** Playwright (Firefox) für Widget-Scraping
* **Datenbank:** SQLite3
* **Audio:** Pygame Mixer
* **Packaging:** PyInstaller

---

## ️ Installation & Build

1.  **Umgebung aufsetzen:**
    ```powershell
    python -m venv .venv
    .\.venv\Scripts\Activate.ps1
    pip install flask requests pillow pygame numpy pynput playwright
    python -m playwright install firefox
    ```

2.  **Starten:**
    ```powershell
    python main.py
    ```

3.  **Kompilieren (.exe):**
    ```powershell
    pyinstaller StreamForge.spec --clean --noconfirm
    ```

---

##  Roadmap / Todo´s
- [X] **Grafik:** Like-Overlay Design auf Neon-Grün umstellen.
- [X] **Features:** Likes als Summe im Timer-Modul integrieren.
- [x] **Stabilität:** Blackout-Modus verbessern und Übergänge optimieren.
- [ ] **Twitch:** Umfassende Tests der Bit-Integration.
- [x] **Bugfix:** Chat-Befehle (Commands) finalisieren und Cooldowns prüfen.
- [x] **Erweiterung:** Unterstützung für weitere Videoformate im Asset-Ordner.
- [ ] **Dokumentation:** Detaillierte Anleitung für das Einrichten der Twitch-API-Keys.

---
*Entwickelt mit Leidenschaft für die Streaming-Community.*