let lastTimestamp = 0;
const DISPLAY_DURATION = 5000; // Anzeigedauer in Millisekunden (5 Sekunden)
let hideTimeout = null;

async function checkActivePlace() {
    try {
        // Cache-Busting (?t=...) damit der Browser nicht die alte Datei lädt
        const response = await fetch('active.json?t=' + new Date().getTime());
        if (!response.ok) return;

        const data = await response.json();

        // Prüfen, ob Daten da sind UND ob sie neu sind (Timestamp Vergleich)
        if (data.timestamp && data.timestamp > lastTimestamp) {
            lastTimestamp = data.timestamp;
            showOverlay(data.user_name, data.place);
        }

    } catch (e) {
        // Fehler ignorieren (z.B. wenn Datei gerade geschrieben wird)
        console.log("Warte auf Daten...");
    }
}

function showOverlay(user, place) {
    const card = document.getElementById('place-card');
    const userEl = document.getElementById('user-name');
    const placeEl = document.getElementById('place-number');
    const progressBar = document.querySelector('.progress-bar');

    // Daten setzen
    userEl.innerText = user;
    placeEl.innerText = "#" + place;

    // Falls schon ein Timeout läuft (schnelle Befehle hintereinander), löschen
    if (hideTimeout) clearTimeout(hideTimeout);

    // Reset Progress Bar für Animation
    progressBar.style.transition = 'none';
    progressBar.style.width = '0%';

    // Kurze Verzögerung, damit der Browser den Style-Reset mitbekommt
    setTimeout(() => {
        // Einblenden
        card.classList.add('show');

        // Progress Bar starten
        progressBar.style.transition = `width ${DISPLAY_DURATION}ms linear`;
        progressBar.style.width = '100%';
    }, 50);

    // Timer zum Ausblenden setzen
    hideTimeout = setTimeout(() => {
        card.classList.remove('show');
    }, DISPLAY_DURATION);
}

// Alle 1 Sekunde prüfen, ob ein neuer Befehl da ist
setInterval(checkActivePlace, 1000);