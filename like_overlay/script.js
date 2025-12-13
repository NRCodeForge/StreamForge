const API_URL = 'http://127.0.0.1:5000/api/v1/like_challenge';
const challengeTextElement = document.getElementById('challenge-text');
// Falls du eine Progress-Bar im HTML hast (optional):
const progressBarElement = document.getElementById('progress-bar');

async function updateChallenge() {
    try {
        const response = await fetch(API_URL);
        const data = await response.json();

        if (data.error) {
            console.error("Server Error:", data.error);
            return;
        }

        // 1. TEXT ANZEIGEN
        // Wir prüfen, ob der Server uns einen formatierten Text ("display_text") schickt.
        // Falls ja, nehmen wir den. Falls nein, bauen wir einen Fallback.
        if (data.display_text) {
            challengeTextElement.textContent = data.display_text;
        } else {
            // Fallback, falls "display_text" fehlt
            const current = data.current_likes || 0;
            const goal = data.goal || 1;
            challengeTextElement.textContent = `${current} / ${goal}`;
        }

        // 2. PROGRESS BAR (Falls vorhanden)
        if (progressBarElement) {
            const current = data.current_likes || 0;
            const goal = data.goal || 1;
            const percent = Math.min((current / goal) * 100, 100);
            progressBarElement.style.width = percent + "%";
        }

        // Optional: Automatische Reload bei neuem Ziel (Sound wird vom Python-Backend abgespielt)

    } catch (error) {
        console.error("Verbindungsfehler:", error);
    }
}

// Starten
updateChallenge();
setInterval(updateChallenge, 1000); // Jede Sekunde aktualisieren