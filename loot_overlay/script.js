// 1. Socket-Verbindung initialisieren
const socket = io();

// 2. HTML-Elemente referenzieren (IDs passend zu deinem HTML)
const video = document.getElementById('loot-video');
const container = document.getElementById('overlay-container');
const textElement = document.getElementById('prompt-text');

// 3. Auf das Event "loot_event" hören
socket.on('loot_event', function(data) {
    console.log("Event empfangen für Mode:", data.mode);
    console.log("Prompt:", data.prompt);

    // Sicherheitscheck: Existieren die Elemente im DOM?
    if (!video || !container || !textElement) {
        console.error("Konnte HTML-Elemente nicht finden. Bitte IDs prüfen!");
        return;
    }

    // A) Text setzen
    textElement.innerText = data.prompt;

    // B) Video-Quelle dynamisch setzen
    // Nutzt deine Flask-Route: /assets/videos/<mode>.mp4
    const videoUrl = "/assets/videos/" + data.mode + ".mp4";
    video.src = videoUrl;

    // C) Container anzeigen
    container.style.display = "block";

    // D) Video abspielen
    video.currentTime = 0; // Immer von vorne starten
    video.load(); // Wichtig, wenn die src dynamisch geändert wurde

    let playPromise = video.play();

    if (playPromise !== undefined) {
        playPromise.catch(error => {
            console.warn("Autoplay blockiert. Versuche Muted-Play...", error);
            // Browser blocken oft Videos mit Ton. Muted als Fallback:
            video.muted = false;
            video.play();
        });
    }
});

// 4. Wenn das Video zu Ende ist: Overlay ausblenden
if (video) {
    video.onended = function() {
        console.log("Video beendet, blende Overlay aus.");
        if (container) {
            container.style.display = "none";
        }
        // Quelle leeren, um Speicher freizugeben und Standbild zu vermeiden
        video.src = ""; 
    };
}