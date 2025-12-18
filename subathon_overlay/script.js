const settingsUrl = 'settings.json';
const track = document.getElementById('rules-track');

// URL Parameter (?platform=twitch oder ?platform=tiktok)
const urlParams = new URLSearchParams(window.location.search);
const platform = urlParams.get('platform');

const tiktokKeys = ["subscribe", "follow", "coins", "share", "like", "chat"];
const twitchKeys = ["twitch_sub", "twitch_gift", "twitch_msg", "twitch_bits"];

const labels = {
    "subscribe": "Superfan",
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
        const response = await fetch(settingsUrl + '?t=' + new Date().getTime());
        const settings = await response.json();
        updateDisplay(settings);
    } catch (error) {
        console.error("Fehler beim Laden der Regeln:", error);
    }
}

function updateDisplay(settings) {
    const moveContainer = document.querySelector('.ticker-move');

    // Wir sammeln erst alle HTML-Fragmente in einer Liste
    let activeItemsHTML = [];

    // Alle möglichen Regeln durchgehen (Reihenfolge wie im HTML definiert wäre besser,
    // aber da wir hier neu bauen, nehmen wir eine feste Reihenfolge oder iterieren über Keys)
    // Wir nutzen hier die Keys aus Labels, um eine feste Reihenfolge zu haben:
    const allKeys = Object.keys(labels);

    allKeys.forEach(key => {
        // 1. Plattform Check
        let isForCurrentPlatform = true;
        if (platform === 'twitch') {
            if (!twitchKeys.includes(key)) isForCurrentPlatform = false;
        } else if (platform === 'tiktok') {
            if (!tiktokKeys.includes(key)) isForCurrentPlatform = false;
        }

        if (!isForCurrentPlatform) return;

        // 2. Aktiv Check
        let config = settings[key];
        let isActive = false;
        let value = 0;

        if (config && typeof config === 'object' && config.active !== undefined) {
             isActive = config.active;
             value = config.value;
        } else if (settings[key + "_active"]) {
             isActive = settings[key + "_active"];
             value = settings[key + "_value"];
        }

        if (isActive) {
            let name = labels[key] || key;
            // HTML Bauen
            activeItemsHTML.push(
                `<div class="rule-item" data-rule="${key}">` +
                `${name}: <span class="highlight">+${value}s</span>` +
                `</div>`
            );
        }
    });

    if (activeItemsHTML.length === 0) {
        moveContainer.innerHTML = '';
        moveContainer.style.animation = 'none';
        return;
    }

    // 3. TRICK: Inhalt verdoppeln für nahtlosen Loop!
    // Wir fügen die Liste ZWEIMAL ein.
    // [Regel A] [Regel B] ... [Regel A] [Regel B]
    const content = activeItemsHTML.join('') + activeItemsHTML.join('');

    // Nur aktualisieren, wenn sich was geändert hat (verhindert Flackern)
    if (moveContainer.innerHTML !== content) {
        moveContainer.innerHTML = content;

        // Animation sicherstellen
        moveContainer.style.animation = 'none';
        moveContainer.offsetHeight; /* Trigger Reflow */
        // Die Dauer (40s) kannst du anpassen, je nachdem wie schnell es laufen soll
        moveContainer.style.animation = 'ticker 40s linear infinite';
    }
}

loadRules();
setInterval(loadRules, 5000);