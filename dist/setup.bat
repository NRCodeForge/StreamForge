@echo off
title StreamForge - Ersteinrichtung
color 0B

echo ========================================================
echo  StreamForge - Ersteinrichtung
echo ========================================================
echo.
echo Dieses Skript installiert die benoetigten Python-Module
echo und den fuer die "Like Challenge" erforderlichen Browser.
echo.
echo VORAUSSETZUNG: Python 3.x muss auf diesem System
echo installiert und im System-PATH verfuegbar sein.
echo.
echo Start der Installation... Dies kann einige Minuten dauern.
echo Bitte nicht schliessen!
echo.

rem Sicherstellen, dass pip aktuell ist
echo Aktualisiere pip...
python -m pip install --upgrade pip
if %errorlevel% neq 0 (
    echo.
    echo FEHLER: Konnte pip nicht aktualisieren.
    echo Bitte stelle sicher, dass Python installiert ist und 'python' im PATH funktioniert.
    echo Versuche es manuell mit "python -m pip install --upgrade pip".
    pause
    exit /b %errorlevel%
)
echo.

rem Installiere die Python-Abhängigkeiten
echo Installiere Python-Module...
pip install pyinstaller pygame pynput pillow numpy playwright
if %errorlevel% neq 0 (
    echo.
    echo FEHLER: Konnte Python-Module nicht installieren.
    echo Eine detaillierte Fehlermeldung wurde oben ausgegeben.
    echo Bitte ueberpruefe deine Python-Installation und Internetverbindung.
    pause
    exit /b %errorlevel%
)
echo.

rem Lade den Playwright Firefox-Browser herunter
echo Lade den fuer Playwright benoetigten Firefox-Browser herunter...
playwright install firefox
if %errorlevel% neq 0 (
    echo.
    echo FEHLER: Konnte den Playwright Firefox-Browser nicht herunterladen.
    echo Eine detaillierte Fehlermeldung wurde oben ausgegeben.
    echo Bitte ueberpruefe deine Internetverbindung.
    pause
    exit /b %errorlevel%
)
echo.

echo ========================================================
echo  Ersteinrichtung erfolgreich abgeschlossen!
echo ========================================================
echo.
echo Du kannst dieses Fenster jetzt schliessen und "StreamForge.exe" starten.
echo.

pause
exit