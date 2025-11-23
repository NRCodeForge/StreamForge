// API-Endpunkt, der auf active.json schaut
const API_URL = 'http://127.0.0.1:5000/api/v1/commands';
// Wie oft wir nachfragen, ob ein neuer Befehl aktiv ist
const POLLING_INTERVAL_MS = 500; // Jede halbe Sekunde
// Wie lange die Ausblend-Animation dauert (muss zur CSS passen)
const FADE_OUT_DURATION_MS = 500;

// WICHTIG: Diese IDs müssen exakt mit der index.html übereinstimmen
const container = document.getElementById('command-container');
const textElement = document.getElementById('command-text');
const costsElement = document.getElementById('command-costs');

let currentCommandId = null; // Speichert die ID des *aktuell angezeigten* Befehls
let isVisible = false;

async function pollActiveCommand() {
    // Verhindere Fehler, falls die HTML doch falsch geladen wurde
    if (!container || !textElement || !costsElement) {
        console.error("HTML-Elemente (container, text oder costs) nicht gefunden!");
        return;
    }

    try {
        // Cache-Busting, um sicherzustellen, dass wir immer die neueste active.json erhalten
        const response = await fetch(API_URL + '?t=' + new Date().getTime());
        if (!response.ok) {
            throw new Error('API nicht erreichbar');
        }

        const command = await response.json();

        // --- Fall 1: Ein NEUER Befehl ist da ---
        // (Server hat active.json mit einem neuen Befehl gefüllt)
        if (command && command.id && command.id !== currentCommandId) {
            console.log("Neuer Befehl empfangen:", command.text);
            currentCommandId = command.id;
            isVisible = true;

            // Daten füllen (Fehlerquelle 1 behoben)
            textElement.textContent = command.text;
            costsElement.textContent = `${command.costs} Whieties`;

            // Einblenden (Fehlerquelle 2 behoben)
            container.classList.remove('hide');
            container.classList.add('show');
        }
        // --- Fall 2: Der Befehl ist WEG (leeres Objekt {}) und wir zeigen noch was an ---
        // (Server hat active.json geleert, weil die Zeit für den Befehl abgelaufen ist)
        else if ((!command || !command.id) && isVisible) {
            console.log("Befehl ausblenden.");
            isVisible = false;
            currentCommandId = null;

            // Ausblenden (Fehlerquelle 2 behoben)
            container.classList.remove('show');
            container.classList.add('hide');

            // Text leeren, *nachdem* die Animation fertig ist
            setTimeout(() => {
                if (!isVisible) { // Nur wenn nicht schon ein neuer da ist
                     textElement.textContent = "";
                     costsElement.textContent = "";
                }
            }, FADE_OUT_DURATION_MS);
        }

    } catch (error) {
        console.error("Polling-Fehler:", error);
    }
}

// Starte das Polling
console.log("Command Overlay Polling gestartet...");
pollActiveCommand(); // Sofortiger erster Check
setInterval(pollActiveCommand, POLLING_INTERVAL_MS);