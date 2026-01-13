const API_URL = '/api/v1/like_challenge';

// 1. DIESE DEFINITIONEN FEHLTEN:
const challengeTextElement = document.getElementById('challenge-text');
const progressBarElement = document.getElementById('progress-bar');

let lastLikes = -1; 

async function updateChallenge() {
    try {
        const response = await fetch(API_URL);
        const data = await response.json();

        if (data.error) return;

        // Prüfen, ob sich die Likes geändert haben (Animation nur bei echtem Wechsel)
        if (lastLikes !== -1 && data.current_likes !== lastLikes) {
            triggerAnimation();
        }
        lastLikes = data.current_likes;

        // Text aktualisieren
        if (data.display_text) {
            challengeTextElement.textContent = data.display_text;
        } else {
            const current = data.current_likes || 0;
            const goal = data.goal || 1;
            challengeTextElement.textContent = `${current} / ${goal}`;
        }

        // Progress Bar Update
        if (progressBarElement) {
            const percent = Math.min((data.current_likes / data.goal) * 100, 100);
            progressBarElement.style.width = percent + "%";
        }

    } catch (error) {
        console.error("Verbindungsfehler:", error);
    }
}

function triggerAnimation() {
    challengeTextElement.classList.remove('animate-pop');
    void challengeTextElement.offsetWidth; 
    challengeTextElement.classList.add('animate-pop');
}

// 2. DIESER TEIL FEHLTE AUCH (Der eigentliche Start):
updateChallenge(); // Sofort beim Laden einmal ausführen
setInterval(updateChallenge, 1000); // Alle 1000ms (1 Sekunde) wiederholen