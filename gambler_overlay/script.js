let lastTimestamp = 0;
const container = document.getElementById('gambit-container');
const reel = document.getElementById('slot-reel');
const resultBox = document.getElementById('result-box');

// --- QUEUE SYSTEM ---
let animationQueue = [];
let isAnimating = false;

// Confetti Setup (Erstellt Container falls nicht vorhanden)
let confettiContainer = document.getElementById('confetti-layer');
if (!confettiContainer) {
    confettiContainer = document.createElement('div');
    confettiContainer.id = 'confetti-layer';
    confettiContainer.style.cssText = "position: absolute; top:0; left:0; width:100%; height:100%; pointer-events:none; z-index: 1; overflow: hidden;";
    document.body.insertBefore(confettiContainer, document.body.firstChild);
}

// Visuelle Items
const slotItems = [
    "KAMMER 1", "KAMMER 2", "KAMMER 3", "KAMMER 4", "KAMMER 5", "KAMMER 6",
    "KAMMER 1", "KAMMER 2", "KAMMER 3", "KAMMER 4", "KAMMER 5", "KAMMER 6"
];
const ITEM_HEIGHT = 100;

// 1. POLLING (API abfragen)
async function pollAPI() {
    try {
        const response = await fetch('/api/v1/events/gambler/next');
        if (!response.ok) return;

        const data = await response.json();

        if (Object.keys(data).length > 0 && data.chamber) {
            console.log("Event von API erhalten:", data);
            animationQueue.push(data);
        }
    } catch (e) { }
}

// 2. QUEUE CHECKER
function checkQueue() {
    if (!isAnimating && animationQueue.length > 0) {
        const nextEvent = animationQueue.shift();
        playAnimation(nextEvent);
    }
}

// 3. ANIMATION (Alles 50% schneller)
function playAnimation(data) {
    isAnimating = true;

    // UI Reset
    container.classList.add('show');
    resultBox.classList.remove('show');
    resultBox.innerText = "";
    confettiContainer.innerHTML = '';

    let reelContent = "";

    // Kurze Drehung (3 Runden)
    const rounds = 3;
    const totalItems = rounds * slotItems.length;

    for(let i=0; i < totalItems; i++) {
        const txt = slotItems[i % slotItems.length];
        reelContent += `<div class="slot-item">${txt}</div>`;
    }

    const finalText = `KAMMER ${data.chamber}`;
    reelContent += `<div class="slot-item" style="color: #E0E0E0; font-size: 36px; font-weight: bold;">${finalText}</div>`;

    reel.innerHTML = reelContent;
    reel.style.transition = 'none';
    reel.style.top = '0px';

    // Start Drehung
    setTimeout(() => {
        const targetTop = -(totalItems * ITEM_HEIGHT);

        // 2.25 Sekunden Drehung
        reel.style.transition = 'top 2.25s cubic-bezier(0.25, 1, 0.5, 1)';
        reel.style.top = targetTop + 'px';
    }, 100);

    // Ende Drehung & Ergebnis
    setTimeout(() => {
        resultBox.innerText = data.result;
        resultBox.style.color = data.color;
        resultBox.classList.add('show');

        container.style.borderColor = data.color;
        setTimeout(() => container.style.borderColor = 'rgb(222, 11, 50)', 800);

        spawnConfetti();

    }, 2400); // Nach 2,4s ist das Ergebnis da

    // Ausblenden (Gesamtdauer reduziert auf 8s)
    // Das bedeutet: ca. 2,4s Spin + 5,6s Anzeige des Ergebnisses
    setTimeout(() => {
        container.classList.remove('show');

        setTimeout(() => {
            isAnimating = false; // Bereit für nächstes Event
            confettiContainer.innerHTML = '';
        }, 1000);

    }, 6000); // HIER GEÄNDERT: Von 15000 auf 8000 reduziert
}

function spawnConfetti() {
    const colors = ['#ff0000', '#ffffff', '#d4af37', '#222'];
    if (!document.getElementById('confetti-style')) {
        const style = document.createElement('style');
        style.id = 'confetti-style';
        style.innerHTML = `.confetti { position: absolute; width: 12px; height: 12px; opacity: 0; z-index: 5; } @keyframes confetti-fall { 0% { transform: translateY(0) rotate(0deg); opacity: 1; } 100% { transform: translateY(800px) rotate(720deg); opacity: 0; } }`;
        document.head.appendChild(style);
    }

    for (let i = 0; i < 150; i++) {
        const c = document.createElement('div');
        c.classList.add('confetti');
        c.style.left = Math.random() * 100 + 'vw';
        c.style.top = '-20px';
        c.style.backgroundColor = colors[Math.floor(Math.random() * colors.length)];
        c.style.animation = `confetti-fall ${Math.random() * 3 + 2}s linear ${Math.random() * 0.5}s forwards`;
        confettiContainer.appendChild(c);
    }
}

// Loops starten
setInterval(pollAPI, 1000);
setInterval(checkQueue, 200);