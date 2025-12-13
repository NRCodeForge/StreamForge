const API_URL = '/api/v1/timer/state';
const timerElement = document.getElementById('timer'); // Stelle sicher, dass du ein Element mit id="timer" in der HTML hast

async function updateTimer() {
    try {
        const response = await fetch(API_URL);
        const data = await response.json();

        // Zeit formatieren
        const h = String(data.hours).padStart(2, '0');
        const m = String(data.minutes).padStart(2, '0');
        const s = String(data.seconds).padStart(2, '0');

        // Anzeige setzen
        if (timerElement) {
            timerElement.textContent = `${h}:${m}:${s}`;

            // Klassen für Effekte hinzufügen (Hype Train, Frozen etc.)
            document.body.classList.toggle('hype-mode', data.is_hype);
            document.body.classList.toggle('frozen-mode', data.is_frozen);
            document.body.classList.toggle('blind-mode', data.is_blind);
            document.body.classList.toggle('paused', data.is_paused);
        }

    } catch (error) {
        console.error("Timer API Fehler:", error);
    }
}

// Schnell aktualisieren (jede Sekunde oder öfter für flüssige Anzeige)
setInterval(updateTimer, 500);
updateTimer();