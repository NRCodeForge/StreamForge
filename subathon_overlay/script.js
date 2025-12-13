const settingsUrl = 'settings.json';
const container = document.querySelector('.rules-container');

// Mapping für schönere Anzeige-Namen
const labels = {
    "subscribe": "TikTok Abo",
    "follow": "Follow",
    "coins": "1 Coin",
    "share": "Share",
    "like": "Likes",
    "chat": "Chat",
    "twitch_sub": "Twitch Sub",
    "twitch_gift": "Gift Sub",
    "twitch_msg": "Twitch Chat",
    "twitch_bits": "1 Bit"
};

async function loadRules() {
    try {
        const response = await fetch(settingsUrl);
        // Cache-Busting, damit Änderungen sofort sichtbar sind
        const settings = await response.json();
        updateDisplay(settings);
    } catch (error) {
        console.error("Fehler beim Laden der Regeln:", error);
    }
}

function updateDisplay(settings) {
    // Gehe alle HTML-Elemente durch, die eine Regel sein sollen
    document.querySelectorAll('.rule-item').forEach(item => {
        const key = item.getAttribute('data-rule');
        const config = settings[key];

        if (config && config.active) {
            // Element anzeigen
            item.style.display = 'flex';

            // Name und Wert holen
            let name = labels[key] || key;
            let value = config.value;

            // Spezial-Formatierung für Likes (optional, z.B. wenn man kleine Werte hat)
            if (key === 'like' && parseFloat(value) < 1) {
                // Beispiel: Zeige an was 100 Likes bringen, wenn 1 Like zu wenig ist
                // item.innerText = `${name} (100x): +${(value * 100).toFixed(0)}s`;
                // Aber wir bleiben erst mal beim Standard:
                item.innerText = `${name}: +${value}s`;
            } else {
                item.innerText = `${name}: +${value}s`;
            }

            // Falls du CSS-Klassen für Styling brauchst:
            item.classList.add('active-rule');
        } else {
            // Verstecken wenn inaktiv
            item.style.display = 'none';
        }
    });
}

// Initial laden
loadRules();

// Alle 10 Sekunden prüfen, ob sich Settings geändert haben
setInterval(loadRules, 10000);