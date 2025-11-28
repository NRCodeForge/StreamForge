const API_URL = '/api/v1/like_challenge';
const percentageText = document.getElementById('percentage-text');
const container = document.getElementById('bar-container');

let currentGoal = 1;
let currentLikes = 0;
let displayedPercent = 0;

// --- EINSTELLUNGEN ---
let roadSpeed = 3;       // Geschwindigkeit der Straße
let scaleFactor = 1.0;   // ZURÜCK AUF ORIGINALGRÖSSE (1.0)

// --- API Polling ---
async function fetchData() {
    try {
        const response = await fetch(API_URL);
        const data = await response.json();
        if (!data.error) {
            currentLikes = data.like_count;
            currentGoal = data.current_goal;
        }
    } catch (e) { console.error("API Error", e); }
}
setInterval(fetchData, 1000);
fetchData();

// --- LOGGING ---
setInterval(() => {
    const time = new Date().toLocaleTimeString();
    console.log(`[${time}] Status-Check: ${currentLikes} Likes von ${currentGoal} (Ziel)`);
}, 20000);


// --- ROAD & SCRATCH ANIMATION ---

let scratches = [];
let roadOffset = 0;

function setup() {
  let w = container.offsetWidth;
  let h = container.offsetHeight;
  let cnv = createCanvas(w, h);
  cnv.parent('p5-canvas-container');

  // Initial: Keine Kratzer oder nur wenige zufällige, damit es nicht leer aussieht
  for(let i = 0; i < 50; i++) {
      spawnRoadScratch(random(-width, 0));
  }
}

function draw() {
  clear();

  // 1. Fortschritt berechnen
  let targetPercent = (currentLikes / currentGoal) * 100;
  if (targetPercent > 100) targetPercent = 100;
  displayedPercent = lerp(displayedPercent, targetPercent, 0.1);

  if (percentageText) percentageText.innerText = Math.floor(displayedPercent) + "%";

  // Die Position des roten Strichs auf dem Bildschirm
  let progressX = map(displayedPercent, 0, 100, 0, width);

  // 2. Straße bewegen
  roadOffset += roadSpeed;

  // --- RENDERING ---
  drawingContext.save();

  // A) CLIPPING (Maske: Nur links vom Strich sichtbar)
  drawingContext.beginPath();
  drawingContext.rect(0, 0, progressX, height);
  drawingContext.clip();

  // B) Hintergrund & Gitter
  background(10, 10, 12);

  stroke(40, 0, 0, 100);
  strokeWeight(1);

  let gridSpacing = 40;
  let gridShift = roadOffset % gridSpacing;

  // Gitterlinien
  for (let x = -gridShift; x < width; x += gridSpacing) {
      line(x, 0, x, height);
  }
  for (let y = 0; y < height; y += 20) {
      line(0, y, width, y);
  }

  // C) SPAWN LOGIK (NEU: Auf dem Strich!)
  // Wir spawnen Kratzer genau an der aktuellen "Welt-Position" des roten Strichs.
  // Welt-Position = Bildschirmposition (progressX) + Wie weit die Straße schon gefahren ist (roadOffset)

  // Nur spawnen, wenn der Balken überhaupt sichtbar ist (> 1 Pixel)
  if (progressX > 1) {
      let density = 2; // Anzahl pro Frame
      for(let k=0; k<density; k++) {
          // Wir addieren roadOffset, damit der Kratzer an der Stelle auf der Straße "kleben" bleibt
          // Random Y für die Höhe, Random Offset X für leichtes Streuen um den Strich herum
          let spawnWorldX = roadOffset + progressX + random(-5, 2);
          spawnRoadScratch(spawnWorldX);
      }
  }

  // Update & Draw Scratches
  for (let i = scratches.length - 1; i >= 0; i--) {
    scratches[i].update();
    scratches[i].display(roadOffset);

    // Löschen wenn komplett verblasst oder weit links raus
    if (scratches[i].isDead(roadOffset)) {
        scratches.splice(i, 1);
    }
  }

  drawingContext.restore();

  // 3. Rote Linie (Spitze)
  if (displayedPercent > 0.5) {
      stroke(255, 0, 0);
      strokeWeight(2);
      drawingContext.shadowBlur = 10;
      drawingContext.shadowColor = 'red';
      line(progressX, 0, progressX, height);
      drawingContext.shadowBlur = 0;
  }
}

function windowResized() {
    resizeCanvas(container.offsetWidth, container.offsetHeight);
}

function spawnRoadScratch(worldX) {
    let y = random(height);
    scratches.push(new RoadScratch(worldX, y));
}

// --- KLASSEN (Originalgrößen) ---

class RoadScratch {
  constructor(worldX, y) {
    this.worldX = worldX;
    this.y = y;
    // Originalgröße: 15 bis 50
    this.len = random(15, 50);
    this.ang = random(TWO_PI);
    this.opacity = 255;
    this.born = millis();
    this.fragments = [];
  }

  update() {
    let age = millis() - this.born;
    // Sie verblassen und schrumpfen, während sie nach links wandern
    this.opacity = map(age, 0, 4000, 255, 0);
    this.len *= 0.98; // Schrumpfeffekt (Original war 0.99 oder 0.95)

    // Fragmente erzeugen
    if (random(1) < 0.1 && this.opacity > 50) {
      let r = random(this.len);
      let fx = this.worldX + cos(this.ang) * r;
      let fy = this.y + sin(this.ang) * r;
      this.fragments.push(new RoadFragment(fx, fy));
    }

    for (let frag of this.fragments) {
      frag.update();
    }
    this.fragments = this.fragments.filter(f => f.opacity > 0);
  }

  isDead(currentRoadOffset) {
      let screenX = this.worldX - currentRoadOffset;
      return this.opacity <= 0 || screenX < -50;
  }

  display(currentRoadOffset) {
    let screenX = this.worldX - currentRoadOffset;

    push();
    translate(screenX, this.y);
    rotate(this.ang);

    stroke(200, 20, 20, this.opacity);
    strokeWeight(1.5); // Originale Dicke
    line(0, 0, this.len, 0);
    pop();

    for (let frag of this.fragments) {
      frag.display(currentRoadOffset);
    }
  }
}

class RoadFragment {
  constructor(worldX, y) {
    this.worldX = worldX;
    this.y = y;
    this.dx = random(-1, 1);
    this.dy = random(-1, 1);
    this.opacity = 200;
    this.size = random(1, 3); // Originalgröße
  }

  update() {
    this.worldX += this.dx;
    this.y += this.dy;
    this.opacity -= 8; // Schnellerer Fade für Fragmente
  }

  display(currentRoadOffset) {
    let screenX = this.worldX - currentRoadOffset;
    noStroke();
    fill(180, 0, 0, this.opacity);
    ellipse(screenX, this.y, this.size);
  }
}