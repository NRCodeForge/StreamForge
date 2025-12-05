let lastTimestamp = 0;
const container = document.getElementById('gambit-container');
const reel = document.getElementById('slot-reel');


let animationQueue = [];
let isAnimating = false;
let slotItems = ["LOADING..."]; // Standard, wird überschrieben

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
    resultBox.classList.remove('show');
    resultBox.innerText = "";

    let reelContent = "";
    const rounds = 4; // Dreht sich oft
    const totalItems = rounds * slotItems.length;

    for(let i=0; i < totalItems; i++) {
        const txt = slotItems[i % slotItems.length];
        reelContent += `<div class="slot-item">${txt}</div>`;
    }

    // Ergebnis (kommt vom Server als "chamber")
    reelContent += `<div class="slot-item" style="color: #E0E0E0; font-size: 36px; font-weight: bold;">${data.chamber}</div>`;

    reel.innerHTML = reelContent;
    reel.style.transition = 'none';
    reel.style.top = '0px';

    setTimeout(() => {
        const targetTop = -(totalItems * ITEM_HEIGHT);
        reel.style.transition = 'top 2.5s cubic-bezier(0.25, 1, 0.5, 1)';
        reel.style.top = targetTop + 'px';
    }, 100);

    setTimeout(() => {
        resultBox.style.color = data.color;
        resultBox.classList.add('show');
        container.style.borderColor = data.color;
        setTimeout(() => container.style.borderColor = 'rgb(222, 11, 50)', 800);
    }, 2700);

    setTimeout(() => {
        container.classList.remove('show');
        setTimeout(() => {
            isAnimating = false;
        }, 1000);
    }, 8000);
}

setInterval(pollAPI, 1000);
setInterval(checkQueue, 200);