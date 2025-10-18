import subprocess
import json
import os

try:
    # Führe den Playwright-CLI-Befehl aus, um den Pfad zu erhalten
    result = subprocess.run(
        ['playwright', 'browsers', 'path', 'firefox'],
        capture_output=True,
        text=True,
        check=True
    )
    browser_executable_path = result.stdout.strip()

    # Playwright gibt das Excutable direkt zurück,
    # wir brauchen den Ordner, der die Binärdateien enthält.
    # Das ist normalerweise 4 Ebenen höher als das Excutable selbst.
    # Beispiel: .../ms-playwright/firefox-1901/firefox/firefox.exe
    # Wir wollen: .../ms-playwright/firefox-1901

    # Gehe 4 Ebenen nach oben
    browser_root_path = os.path.abspath(os.path.join(browser_executable_path, '....'))

    # Prüfen, ob der Pfad den erwarteten 'ms-playwright' enthält
    if "ms-playwright" in browser_root_path.lower():
        print(f"Der Playwright-Browser-Root-Pfad ist wahrscheinlich: {browser_root_path}")
        print(
            "\nBitte kopieren Sie den Ordner 'ms-playwright' (oder den relevanten 'firefox-<version>' Ordner darin) aus diesem Pfad.")
        print(
            f"Sie finden 'ms-playwright' wahrscheinlich unter: {os.path.abspath(os.path.join(browser_executable_path, '....', '..'))}")
    else:
        print(f"Das Browser-Executable ist hier: {browser_executable_path}")
        print("Der direkte Pfad zum Ordner, den Sie kopieren müssen, könnte sein:")
        # Versuch, den ms-playwright Ordner zu erraten
        likely_ms_playwright_dir = os.path.join(os.path.expanduser('~'), 'AppData', 'Local', 'ms-playwright')
        print(f"Windows Standard: {likely_ms_playwright_dir}")


except subprocess.CalledProcessError as e:
    print(f"Fehler beim Ausführen des Playwright-Befehls: {e}")
    print("Stellen Sie sicher, dass Playwright installiert ist (`pip install playwright`)")
    print("und die Browser heruntergeladen wurden (`playwright install firefox`).")
except FileNotFoundError:
    print("Der Befehl 'playwright' wurde nicht gefunden.")
    print("Stellen Sie sicher, dass Playwright im PATH Ihrer Umgebung ist.")
except Exception as e:
    print(f"Ein unerwarteter Fehler ist aufgetreten: {e}")