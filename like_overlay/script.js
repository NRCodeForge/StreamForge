const API_URL = 'http://127.0.0.1:5000/api/v1/like_challenge';
const challengeTextElement = document.getElementById('challenge-text');

async function updateChallenge() {
    try {
        const response = await fetch(API_URL);
        const data = await response.json();

        // Fehlerbehandlung vom Server
        if (data.error) {
            challengeTextElement.textContent = data.error;
            return;
        }

        // KORREKTUR: Daten aus den richtigen Feldern lesen
        // Python sendet: { "current_likes": 123, "goal": 10000, ... }
        const currentLikes = data.current_likes || 0;
        const goal = data.goal || 10000;

        // Anzeige aktualisieren (Format: "150 / 10000 Likes")
        challengeTextElement.textContent = `${currentLikes} / ${goal} Likes`;

        // Falls du eine Progress-Bar hast, kannst du hier die Breite setzen:
        // const percent = Math.min((currentLikes / goal) * 100, 100);
        // document.getElementById('deine-bar-id').style.width = percent + "%";

    } catch (error) {
        console.error("Fehler beim Abrufen der Challenge-Daten:", error);
        // Bei Fehler nichts überschreiben oder "Offline" anzeigen
    }
}

// Initialer Aufruf
updateChallenge();

// Alle 2 Sekunden aktualisieren (5s ist für Likes oft etwas langsam)
setInterval(updateChallenge, 2000);