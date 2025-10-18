document.addEventListener('DOMContentLoaded', async () => {
    // Lade die Einstellungen von der JSON-Datei
    const settings = await getSettings();
    const allRules = document.querySelectorAll('.rule-item');
    const activeRules = [];

    // Ein Objekt, das die Regel-Namen auf lesbare Texte abbildet.
    const ruleTextMapping = {
        subscribe: "pro Abo / Super Fan",
        follow: "pro Follow",
        coins: "pro Münze",
        share: "pro Teilen",
        like: "pro Like",
        chat: "pro Chat-Nachricht"
    };

    // Gehe alle möglichen Regeln durch (subscribe, follow, etc.)
    for (const key in settings) {
        // Ignoriere die Animationszeit-Einstellung in dieser Schleife
        if (key === 'animations_time' || !settings[key].active) {
            continue;
        }

        // Finde das passende HTML-Element
        const ruleElement = document.querySelector(`.rule-item[data-rule="${key}"]`);
        if (ruleElement) {
            // Kombiniere den Wert aus der JSON mit dem Beschreibungstext
            const valueText = settings[key].value;
            const descriptionText = ruleTextMapping[key] || ''; // Fallback

            ruleElement.textContent = `${valueText} ${descriptionText}`;
            activeRules.push(ruleElement);
        }
    }

    // Entferne alle HTML-Elemente für inaktive Regeln
    allRules.forEach(element => {
        if (!activeRules.includes(element)) {
            element.remove();
        }
    });

    // Starte die Animation nur, wenn es aktive Regeln gibt
    if (activeRules.length > 0) {
        const animationSeconds = parseFloat(settings.animations_time) || 5;
        animateRules(activeRules, animationSeconds * 1000);
    }
});

/**
 * Lädt die Einstellungen aus der settings.json.
 * @returns {Promise<Object>} Ein Promise, das die Einstellungen zurückgibt.
 */
async function getSettings() {
    try {
        const response = await fetch('settings.json');
        if (!response.ok) {
            console.error("settings.json nicht gefunden, verwende Standardwerte.");
            return getDefaultSettings();
        }
        return await response.json();
    } catch (error) {
        console.error("Fehler beim Laden der Einstellungen, verwende Standardwerte.", error);
        return getDefaultSettings();
    }
}

/**
 * Gibt Standardeinstellungen zurück, falls die JSON nicht geladen werden kann.
 * @returns {Object} Die Standardeinstellungen.
 */
function getDefaultSettings() {
    return {
        "animations_time": "5",
        "subscribe": { "value": "Standard: +1 pro Abo", "active": true },
        "follow": { "value": "Standard: +1 pro Follow", "active": true }
    };
}

/**
 * Animiert die Anzeige der Regeln im Wechsel.
 * @param {HTMLElement[]} rules - Ein Array der zu animierenden HTML-Elemente.
 * @param {number} displayDuration - Die Anzeigedauer pro Regel in Millisekunden.
 */
function animateRules(rules, displayDuration) {
    let currentIndex = 0;

    function cycle() {
        if (rules.length === 0) return;

        // Verstecke die vorherige Regel
        const previousIndex = (currentIndex === 0) ? rules.length - 1 : currentIndex - 1;
        rules[previousIndex].classList.remove('show');
        rules[previousIndex].classList.add('hide');

        // Zeige die aktuelle Regel mit der Animation
        const currentRule = rules[currentIndex];
        currentRule.classList.remove('hide');
        currentRule.classList.add('show');

        currentIndex = (currentIndex + 1) % rules.length;

        setTimeout(cycle, displayDuration);
    }

    cycle();
}