document.addEventListener('DOMContentLoaded', async () => {
    const settings = await getSettings();
    const allRules = document.querySelectorAll('.rule-item');
    const activeRules = [];

    const ruleTextMapping = {
        subscribe: " pro TikTok Abo",
        twitch_sub: " pro Twitch Sub",
        follow: " pro Follow",
        coins: " pro Münze",
        share:  "pro Teilen",
        like: " pro Like",
        chat: " pro Nachricht"
    };

    for (const key in settings) {
        if (key === 'animations_time' || key === 'start_time_seconds') continue;

        // Prüfe auf Existenz UND "visible" Property (nicht active!)
        // active steuert den Timer, visible steuert die Anzeige hier.
        const conf = settings[key];
        if (!conf || !conf.visible) continue;

        const ruleElement = document.querySelector(`.rule-item[data-rule="${key}"]`);
        if (ruleElement) {
            // Wert (z.B. "10") und Einheit (Sek) + Text
            // Da in Settings jetzt nur die Zahl steht, fügen wir "Sek" hinzu, falls nötig
            let val = conf.value;
            // Falls alte Config "10 Seconds" hat, bereinigen
            if(val.toString().includes(" ")) val = val.split(" ")[0];

            const descriptionText = ruleTextMapping[key] || key;
            ruleElement.textContent = `+ ${val} Sekunden ${descriptionText}`;
            activeRules.push(ruleElement);
        }
    }

    allRules.forEach(element => {
        if (!activeRules.includes(element)) element.style.display = 'none';
    });

    if (activeRules.length > 0) {
        const animTime = parseFloat(settings.animations_time) || 5;
        animateRules(activeRules, animTime * 1000);
    } else {
        const container = document.querySelector('.rules-container');
        if(container) container.innerHTML = '<div class="rule-item show" style="position:static">Subathon</div>';
    }
});

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