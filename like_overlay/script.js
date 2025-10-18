const API_URL = 'http://127.0.0.1:5000/api/v1/like_challenge';
const challengeTextElement = document.getElementById('challenge-text');

async function updateChallenge() {
    try {
        const response = await fetch(API_URL);
        const data = await response.json();

        if (data.error) {
            challengeTextElement.textContent = data.error;
        } else {
            challengeTextElement.textContent = data.displayText;
        }

    } catch (error) {
        console.error("Fehler beim Abrufen der Challenge-Daten:", error);
        challengeTextElement.textContent = 'Verbindung fehlgeschlagen';
    }
}

updateChallenge();
setInterval(updateChallenge, 5000); // Alle 5 Sekunden aktualisieren