document.addEventListener('DOMContentLoaded', async () => {
    // Lade die Einstellungen
    const settings = await getSettings();
    const allRules = document.querySelectorAll('.rule-item');
    const activeRules = [];

    // Text-Mapping für die Anzeige
    const ruleTextMapping = {
        subscribe: "pro TikTok Abo",
        twitch_sub: "pro Twitch Sub",
        follow: "pro Follow",
        coins: "pro Münze",
        share: "pro Teilen",
        like: "pro Like",
        chat: "pro Nachricht"
    };

    // Gehe durch die Settings
    for (const key in settings) {
        // Ignoriere System-Keys
        if (key === 'animations_time' || !settings[key] || !settings[key].active) {
            continue;
        }

        // Finde das Element im HTML
        const ruleElement = document.querySelector(`.rule-item[data-rule="${key}"]`);
        
        if (ruleElement) {
            // Wert (z.B. "10 Seconds") und Text kombinieren
            const valueText = settings[key].value;
            const descriptionText = ruleTextMapping[key] || key;

            ruleElement.textContent = `${valueText} ${descriptionText}`;
            activeRules.push(ruleElement);
        }
    }

    // Nicht aktive entfernen
    allRules.forEach(element => {
        if (!activeRules.includes(element)) {
            element.style.display = 'none';
        }
    });

    // Animation starten
    if (activeRules.length > 0) {
        const animationSeconds = parseFloat(settings.animations_time) || 5;
        animateRules(activeRules, animationSeconds * 1000);
    } else {
        // Fallback, wenn nichts aktiv ist
        const container = document.querySelector('.rules-container');
        if(container) container.innerHTML = '<div class="rule-item show" style="position:static">Subathon</div>';
    }
});

async function getSettings() {
    try {
        // Fügt Timestamp hinzu, um Caching zu verhindern
        const response = await fetch('settings.json?t=' + new Date().getTime());
        if (!response.ok) return getDefaultSettings();
        return await response.json();
    } catch (error) {
        console.error(error);
        return getDefaultSettings();
    }
}

function getDefaultSettings() {
    return {
        "animations_time": "5",
        "follow": { "value": "+30 Sek", "active": true }
    };
}

function animateRules(rules, displayDuration) {
    let currentIndex = 0;

    // Alle erst ausblenden
    rules.forEach(r => {
        r.classList.remove('show');
        r.classList.add('hide');
    });

    function cycle() {
        if (rules.length === 0) return;

        // Vorherigen ausblenden
        const previousIndex = (currentIndex === 0) ? rules.length - 1 : currentIndex - 1;
        rules[previousIndex].classList.remove('show');
        rules[previousIndex].classList.add('hide');

        // Aktuellen einblenden
        const currentRule = rules[currentIndex];
        currentRule.classList.remove('hide');
        currentRule.classList.add('show');

        // Index hochzählen
        currentIndex = (currentIndex + 1) % rules.length;

        setTimeout(cycle, displayDuration);
    }

    // Start
    cycle();
}