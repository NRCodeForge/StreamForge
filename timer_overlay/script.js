const API_URL = '/api/v1/timer/state';
const timerElement = document.getElementById('timer');

async function updateTimer() {
    try {
        const response = await fetch(API_URL);
        const data = await response.json();

        if (timerElement) {
            // Zeige Zeit an
            timerElement.textContent = `${data.hours}:${data.minutes}:${data.seconds}`;

            // Wenn pausiert: Blinken oder Ausgrauen
            if (data.is_paused) {
                timerElement.style.opacity = "0.5";
            } else {
                timerElement.style.opacity = "1.0";
            }
        }
    } catch (e) {
        console.error("Fehler beim Timer-Update:", e);
    }
}

// Jede Sekunde aktualisieren
setInterval(updateTimer, 1000);
updateTimer();