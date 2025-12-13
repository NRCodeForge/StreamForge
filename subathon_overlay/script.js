const canvas = document.getElementById('wheelCanvas');
const ctx = canvas.getContext('2d');
const container = document.getElementById('wheel-container');

// KONFIGURATION: Wo ist der Pfeil?
// 0   = Rechts (3 Uhr)
// 90  = Unten (6 Uhr)
// 180 = Links (9 Uhr)
// 270 = Oben (12 Uhr) -> Standard
const POINTER_ANGLE = 270;

let isSpinning = false;
let currentRotation = 0;
let lastTimestamp = 0;

// Polling Loop
setInterval(checkState, 1000);

async function checkState() {
    try {
        const res = await fetch('/api/v1/wheel/state');
        const data = await res.json();

        if (data.timestamp && (!isSpinning || data.timestamp !== lastTimestamp)) {
            if (data.timestamp !== lastTimestamp) {
                lastTimestamp = data.timestamp;
                startSpin(data);
            }
        }
    } catch (e) {
        console.error("Polling error", e);
    }
}

function startSpin(data) {
    isSpinning = true;
    container.classList.remove('hidden');

    const segments = data.segments;
    const targetIndex = data.target_index; // Index im Array
    const pfpUrl = data.pfp;
    const bet = data.bet;

    // Debugging Ausgabe in die Konsole (F12 im Browser drücken)
    console.log("Ziel Index:", targetIndex, "Wert:", segments[targetIndex].text);

    // Bild laden
    const img = new Image();
    img.src = pfpUrl || "https://static-cdn.jtvnw.net/user-default-pictures-uv/cdd517fe-def4-11e9-948e-784f43822e80-profile_image-300x300.png";
    img.crossOrigin = "Anonymous";

    // --- BERECHNUNG DER ROTATION ---
    const numSegments = segments.length;
    const anglePerSegment = 360 / numSegments;

    // Wir berechnen den Winkel zur Mitte des Ziel-Segments
    // Wichtig: Segmente werden im Uhrzeigersinn gezeichnet (Index 0 startet bei 0°)
    const segmentCenterAngle = (targetIndex * anglePerSegment) + (anglePerSegment / 2);

    // Ziel: Das Rad muss so gedreht sein, dass 'segmentCenterAngle' genau auf 'POINTER_ANGLE' liegt.
    // Formel: Neuer_Winkel = (Pointer_Pos - Segment_Pos)
    // Beispiel: Ziel bei 15°, Pointer bei 270°. Drehung = 270 - 15 = 255°.
    let targetRotation = POINTER_ANGLE - segmentCenterAngle;

    // Füge viele Umdrehungen hinzu für den Spin-Effekt (mindestens 5 volle)
    const spins = 360 * (5 + Math.floor(Math.random() * 3));
    const endRotation = spins + targetRotation;

    const duration = 6000; // Etwas länger drehen (6s)
    const startTime = performance.now();

    // Startwinkel sauber modulo 360 halten, damit er nicht unendlich wächst
    const startRot = currentRotation % 360;

    function animate(now) {
        const elapsed = now - startTime;
        const progress = Math.min(elapsed / duration, 1);

        // Easing: Cubic Out (schnell start, langsam ende)
        const ease = 1 - Math.pow(1 - progress, 3);

        const currentAngle = startRot + (endRotation - startRot) * ease;

        // Umrechnung in Radians für Canvas
        const currentRad = currentAngle * (Math.PI / 180);

        drawWheel(segments, currentRad, img, bet);

        if (progress < 1) {
            requestAnimationFrame(animate);
        } else {
            // Spin beendet
            currentRotation = currentAngle;

            // Debugging: Prüfen ob es optisch stimmt
            console.log("Fertig. Angezeigter Wert sollte sein:", segments[targetIndex].text);

            // Nach 3 Sek ausblenden
            setTimeout(() => {
                container.classList.add('hidden');
                isSpinning = false;
            }, 3000);
        }
    }
    requestAnimationFrame(animate);
}

function drawWheel(segments, rotation, pfpImage, bet) {
    const cx = canvas.width / 2;
    const cy = canvas.height / 2;
    const radius = cx - 20; // Etwas Rand lassen
    const num = segments.length;
    const step = (2 * Math.PI) / num;

    ctx.clearRect(0, 0, canvas.width, canvas.height);

    ctx.save();
    ctx.translate(cx, cy);
    ctx.rotate(rotation);

    for (let i = 0; i < num; i++) {
        ctx.beginPath();
        ctx.moveTo(0, 0);
        ctx.arc(0, 0, radius, i * step, (i + 1) * step);
        ctx.fillStyle = segments[i].color;
        ctx.fill();
        ctx.lineWidth = 2;
        ctx.strokeStyle = "#fff"; // Weißer Rand zwischen Segmenten
        ctx.stroke();

        // Text zeichnen
        ctx.save();
        ctx.rotate(i * step + step / 2);
        ctx.textAlign = "right";
        ctx.fillStyle = "#fff";
        ctx.font = "bold 20px Arial"; // Schriftgröße etwas angepasst

        // Textschatten für bessere Lesbarkeit
        ctx.shadowColor = "rgba(0,0,0,0.5)";
        ctx.shadowBlur = 4;
        ctx.shadowOffsetX = 2;
        ctx.shadowOffsetY = 2;

        let label = segments[i].text;
        // Text etwas weiter innen positionieren (radius - 40)
        ctx.fillText(label, radius - 40, 8);
        ctx.restore();
    }
    ctx.restore();

    // Profilbild in der Mitte
    ctx.save();
    ctx.beginPath();
    ctx.arc(cx, cy, 60, 0, Math.PI * 2);
    ctx.clip();

    // Hintergrund für PFP falls transparent
    ctx.fillStyle = "#2c3e50";
    ctx.fill();

    try {
        ctx.drawImage(pfpImage, cx - 60, cy - 60, 120, 120);
    } catch(e) {
        // Fallback
    }
    ctx.restore();

    // Goldener Rand ums Bild
    ctx.beginPath();
    ctx.arc(cx, cy, 60, 0, Math.PI * 2);
    ctx.lineWidth = 6;
    ctx.strokeStyle = "#f1c40f"; // Gold/Gelb
    ctx.stroke();

    // Äußerer Rand des Rades
    ctx.beginPath();
    ctx.arc(cx, cy, radius, 0, Math.PI * 2);
    ctx.lineWidth = 4;
    ctx.strokeStyle = "#ecf0f1";
    ctx.stroke();
}