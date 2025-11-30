const API_URL = '/api/v1/timer/state';
const timerElement = document.getElementById('timer');

function updateTimer() {
    fetch('/api/v1/timer/state')
        .then(response => response.json())
        .then(data => {
            // Zeit formatieren (wie gehabt)
            // ... (dein bestehender Code für h/m/s) ...

            const h = String(data.hours).padStart(2, '0');
            const m = String(data.minutes).padStart(2, '0');
            const s = String(data.seconds).padStart(2, '0');

            document.getElementById('timer').innerText = `${h}:${m}:${s}`;

            // --- NEU: Event-Status prüfen ---
            const container = document.body; // Oder dein Haupt-Div

            // Blackout / Blind Mode
            if (data.is_blind) {
                container.classList.add('blind-mode');
            } else {
                container.classList.remove('blind-mode');
            }

            // Optional: Farben ändern bei Hype oder Freezer
            if (data.is_frozen) {
                document.getElementById('timer').style.color = "#00ccff"; // Eisblau
            } else if (data.is_hype) {
                document.getElementById('timer').style.color = "#ffcc00"; // Gold
            } else {
                document.getElementById('timer').style.color = "white"; // Reset
            }
        })
        .catch(err => console.error(err));
}

// Jede Sekunde aktualisieren
setInterval(updateTimer, 1000);
updateTimer();