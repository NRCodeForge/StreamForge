const canvas = document.getElementById('wheelCanvas');
const ctx = canvas.getContext('2d');
const container = document.getElementById('wheel-container');
const winMsg = document.getElementById('winner-msg');
const winAmountSpan = document.getElementById('win-amount');

let isSpinning = false;
let currentRotation = 0;
let lastTimestamp = 0;

// Polling Loop
setInterval(checkState, 1000);

async function checkState() {
    try {
        const res = await fetch('/api/v1/wheel/state');
        const data = await res.json();

        // Wenn Daten da sind und wir noch nicht drehen (oder es ein neuer Spin ist)
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
    winMsg.classList.add('hidden');

    const segments = data.segments;
    const targetIndex = data.target_index;
    const pfpUrl = data.pfp;
    const bet = data.bet;
    const winAmount = data.win_amount;

    // Bild laden
    const img = new Image();
    img.src = pfpUrl || "https://static-cdn.jtvnw.net/user-default-pictures-uv/cdd517fe-def4-11e9-948e-784f43822e80-profile_image-300x300.png";
    img.crossOrigin = "Anonymous";

    // Berechnung der Rotation
    // Pointer ist OBEN (270 Grad / 1.5 PI).
    // Wir wollen, dass das Target Segment oben landet.
    const numSegments = segments.length;
    const anglePerSegment = 360 / numSegments;
    const targetAngle = targetIndex * anglePerSegment + (anglePerSegment / 2); // Mitte des Segments

    // Zufällige volle Drehungen (z.B. 5-8)
    const spins = 360 * (5 + Math.floor(Math.random() * 3));

    // Ziel: Pointer (270) - TargetAngle. Da wir Canvas drehen, müssen wir ENTGEGEN drehen oder Ziel berechnen.
    // Einfacher: Wir drehen das Rad. Damit Segment X oben ist, muss das Rad um (270 - SegmentWinkel) gedreht sein.
    const endRotation = spins + (270 - targetAngle);

    const duration = 5000; // 5 Sekunden
    const startTime = performance.now();
    const startRot = currentRotation % 360;

    function animate(now) {
        const elapsed = now - startTime;
        const progress = Math.min(elapsed / duration, 1);

        // Easing: Cubic Out
        const ease = 1 - Math.pow(1 - progress, 3);

        const currentAngle = startRot + (endRotation - startRot) * ease;
        const currentRad = currentAngle * (Math.PI / 180);

        drawWheel(segments, currentRad, img, bet);

        if (progress < 1) {
            requestAnimationFrame(animate);
        } else {
            // Fertig
            currentRotation = currentAngle;
            showWin(winAmount);

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
    const radius = cx - 20;
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
        ctx.strokeStyle = "#fff";
        ctx.stroke();

        // Text
        ctx.save();
        ctx.rotate(i * step + step / 2);
        ctx.textAlign = "right";
        ctx.fillStyle = "#fff";
        ctx.font = "bold 24px Arial";
        ctx.shadowColor = "black";
        ctx.shadowBlur = 4;

        // Zeige entweder Multiplikator oder absoluten Gewinn
        let label = segments[i].text;
        // Optional: Zeige potenziellen Gewinn statt "2x"
        // label = Math.floor(bet * segments[i].value);

        ctx.fillText(label, radius - 30, 10);
        ctx.restore();
    }
    ctx.restore();

    // Center Image (PFP)
    ctx.save();
    ctx.beginPath();
    ctx.arc(cx, cy, 60, 0, Math.PI * 2);
    ctx.clip();
    try {
        ctx.drawImage(pfpImage, cx - 60, cy - 60, 120, 120);
    } catch(e) {
        ctx.fillStyle = "#333";
        ctx.fill();
    }
    ctx.restore();

    // Rand ums Bild
    ctx.beginPath();
    ctx.arc(cx, cy, 60, 0, Math.PI * 2);
    ctx.lineWidth = 5;
    ctx.strokeStyle = "#fff";
    ctx.stroke();
}

function showWin(amount) {
    winAmountSpan.innerText = amount;
    winMsg.classList.remove('hidden');
}