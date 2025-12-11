let currentConfigSignature = "";

document.addEventListener('DOMContentLoaded', async () => {
    // Initial Load
    await loadAndRender();

    // Polling alle 2 Sekunden
    setInterval(loadAndRender, 2000);
});

async function loadAndRender() {
    const settings = await getSettings();
    const urlParams = new URLSearchParams(window.location.search);
    const platformFilter = urlParams.get('platform'); // 'tiktok', 'twitch' oder null

    // Generiere eine "Signatur" der relevanten Settings, um Änderungen zu erkennen
    const newSignature = generateConfigSignature(settings, platformFilter);

    // Wenn sich nichts geändert hat, brechen wir ab (kein DOM Update)
    if (newSignature === currentConfigSignature) return;

    // Wenn es die erste Ladung ist oder sich was geändert hat:
    if (currentConfigSignature !== "" && currentConfigSignature !== newSignature) {
        // Falls wir eine robuste Methode hätten, würden wir nur Text updaten.
        // Da sich die Animation aber auf die Anzahl der Elemente stützt: Reload ist am sichersten.
        window.location.reload();
        return;
    }

    currentConfigSignature = newSignature;
    updateRules(settings, platformFilter);
}

function generateConfigSignature(settings, platform) {
    // Erstellt einen String aus den Werten und Active-States der Regeln
    const keysToCheck = [
        "subscribe", "follow", "coins", "share", "like", "chat",
        "twitch_sub", "twitch_gift", "twitch_msg", "twitch_bits"
    ];
    let sig = "";
    keysToCheck.forEach(key => {
        let val = 0;
        let act = false;

        if (settings[key] && typeof settings[key] === 'object') {
            val = settings[key].value;
            act = settings[key].active;
        } else if (settings[key + "_value"] !== undefined) {
            val = settings[key + "_value"];
            act = settings[key + "_active"];
        }

        // Füge zur Signatur hinzu, wenn es für die Plattform relevant ist
        // Einfacher: Immer alles prüfen, da eine Änderung in Twitch settings nicht TikTok overlay stört
        // Aber für den Reload Trigger müssen wir spezifisch sein? Nein, settings.json ist global.
        sig += `${key}:${val}:${act}|`;
    });
    return sig + (settings.animations_time || "5");
}

function updateRules(settings, platformFilter) {
    const allRules = document.querySelectorAll('.rule-item');
    const activeRules = [];

    const rulesConfig = [
        { id: 'subscribe',  platform: 'tiktok', label: " pro TikTok Abo" },
        { id: 'follow',     platform: 'tiktok', label: " pro Follow" },
        { id: 'coins',      platform: 'tiktok', label: " pro Münze" },
        { id: 'share',      platform: 'tiktok', label: " pro Teilen" },
        { id: 'like',       platform: 'tiktok', label: " pro Like" },
        { id: 'chat',       platform: 'tiktok', label: " pro Nachricht" },
        { id: 'twitch_sub', platform: 'twitch', label: " pro Twitch Sub" },
        { id: 'twitch_gift',platform: 'twitch', label: " pro Gift Sub" },
        { id: 'twitch_msg', platform: 'twitch', label: " pro Nachricht" },
        { id: 'twitch_bits',platform: 'twitch', label: " pro Bit" }
    ];

    rulesConfig.forEach(rule => {
        if (platformFilter && rule.platform !== platformFilter) return;

        let isActive = false;
        let value = 0;

        if (settings[rule.id] && typeof settings[rule.id] === 'object') {
            isActive = settings[rule.id].active === true || settings[rule.id].visible === true;
            value = settings[rule.id].value;
        } else if (settings[`${rule.id}_active`] !== undefined) {
            isActive = settings[`${rule.id}_active`] === true || settings[`${rule.id}_active`] === 1;
            value = settings[`${rule.id}_value`];
        }

        const ruleElement = document.querySelector(`.rule-item[data-rule="${rule.id}"]`);

        if (isActive && ruleElement && parseFloat(value) > 0) {
            let displayVal = value.toString().split(" ")[0];
            ruleElement.textContent = `+ ${displayVal} Sek.${rule.label}`;
            activeRules.push(ruleElement);
        }
    });

    allRules.forEach(element => {
        if (!activeRules.includes(element)) element.style.display = 'none';
        else element.style.display = 'block'; // Sicherstellen, dass sie sichtbar sind
    });

    if (activeRules.length > 0) {
        const animTime = parseFloat(settings.animations_time) || 5;
        animateRules(activeRules, animTime * 1000);
    } else {
        const container = document.querySelector('.rules-container');
        let fallbackText = "Subathon";
        if (platformFilter === 'tiktok') fallbackText = "Warte auf TikTok Events...";
        if (platformFilter === 'twitch') fallbackText = "Warte auf Twitch Events...";

        container.innerHTML = `<div class="rule-item show" style="position:static; font-size: 0.8em; opacity: 0.7;">${fallbackText}</div>`;
    }
}

async function getSettings() {
    try {
        const r = await fetch('settings.json?t=' + new Date().getTime());
        if (!r.ok) return {};
        return await r.json();
    } catch { return {}; }
}

function animateRules(rules, duration) {
    let index = 0;
    rules.forEach(r => { r.classList.remove('show'); r.classList.add('hide'); });

    function cycle() {
        if (rules.length === 0) return;
        const prev = (index === 0) ? rules.length - 1 : index - 1;
        rules[prev].classList.remove('show');
        rules[prev].classList.add('hide');

        const curr = rules[index];
        curr.classList.remove('hide');
        curr.classList.add('show');

        index = (index + 1) % rules.length;
        setTimeout(cycle, duration);
    }
    cycle();
}