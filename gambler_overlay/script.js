let lastTimestamp = 0;
const container = document.getElementById('gambit-container');
const reel = document.getElementById('slot-reel');
// resultBox Referenz entfernt

let animationQueue = [];
let isAnimating = false;
let slotItems = ["LOADING..."];

const ITEM_HEIGHT = 100;

// 1. Optionen laden
async function loadOptions() {
    try {
        const res = await fetch('/api/v1/gambit/options');
        const texts = await res.json();
        if (texts && texts.length > 0) {
            slotItems = [...texts, ...texts]; // Doppeln für mehr Fülle
            console.log("Optionen geladen:", slotItems);
        }
    } catch(e) { console.log("Standard Optionen behalten"); }
}
loadOptions();

// 2. Polling
async function pollAPI() {
    try {
        const response = await fetch('/api/v1/events/gambler/next');
        if (!response.ok) return;
        const data = await response.json();
        if (Object.keys(data).length > 0 && data.chamber) {
            animationQueue.push(data);
        }
    } catch (e) { }
}

function checkQueue() {
    if (!isAnimating && animationQueue.length > 0) {
        const nextEvent = animationQueue.shift();
        playAnimation(nextEvent);
    }
}

function playAnimation(data) {
    isAnimating = true;
    container.classList.add('show');

    // Standard Border Farbe am Anfang
    container.style.borderColor = 'rgb(222, 11, 50)';

    let reelContent = "";
    const rounds = 4; // Anzahl der Drehungen
    const totalItems = rounds * slotItems.length;

    // Fülle das Rad mit Dummy-Items
    for(let i=0; i < totalItems; i++) {
        const txt = slotItems[i % slotItems.length];
        reelContent += `<div class="slot-item">${txt}</div>`;
    }

    // Das TATSÄCHLICHE Ergebnis als letztes Element anhängen
    // Dies ist das "Roulette"-Ergebnis, das stehen bleibt.
    reelContent += `<div class="slot-item" style="color: ${data.color || '#E0E0E0'}; font-size: 36px; font-weight: bold;">${data.chamber}</div>`;

    reel.innerHTML = reelContent;
    reel.style.transition = 'none';
    reel.style.top = '0px';

    // Animation starten
    setTimeout(() => {
        const targetTop = -(totalItems * ITEM_HEIGHT);
        reel.style.transition = 'top 2.5s cubic-bezier(0.25, 1, 0.5, 1)';
        reel.style.top = targetTop + 'px';
    }, 100);

    // Nach Ende der Drehung (ca. 2.5s) Rahmenfarbe ändern, aber KEINE extra Box anzeigen
    setTimeout(() => {
        container.style.borderColor = data.color; // Rahmenfarbe passend zum Ergebnis
    }, 2700);

    // Ausblenden nach 8 Sekunden
    setTimeout(() => {
        container.classList.remove('show');
        setTimeout(() => {
            isAnimating = false;
        }, 1000);
    }, 8000);
}

setInterval(pollAPI, 1000);
setInterval(checkQueue, 200);