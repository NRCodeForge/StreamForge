const api_url = 'http://127.0.0.1:5000/api/v1/wishes';
const wishContainer = document.querySelector('.wish-container');
const wishTextElements = document.querySelectorAll('.wish-text');
const wishUserElements = document.querySelectorAll('.wish-user');

async function getWishes() {
    // Animation neu starten, indem die Klasse kurz entfernt und wieder hinzugefügt wird
    wishContainer.classList.remove('reanimate');
    // Ein kleiner "Trick", um den Browser zu zwingen, die Animation neu zu rendern
    void wishContainer.offsetWidth;
    wishContainer.classList.add('reanimate');

    try {
        const response = await fetch(api_url);
        const data = await response.json();

        if (data.length > 0) {
            // Zeige die Wünsche an
            for (let i = 0; i < 2; i++) {
                if (data[i]) {
                    wishTextElements[i].textContent = data[i].wunsch;
                    wishUserElements[i].textContent = `~ ${data[i].user_name}`;
                } else {
                    wishTextElements[i].textContent = '';
                    wishUserElements[i].textContent = '';
                }
            }
        } else {
            // Zeige die Leermeldung an
            wishTextElements[0].textContent = "gib !wish <Charakter-Name> ein";
            wishUserElements[0].textContent = "um deinen Charakter zu sehen";
            if (wishTextElements[1]) {
                wishTextElements[1].textContent = '';
                wishUserElements[1].textContent = '';
            }
        }
    } catch (error) {
        console.error("Fehler beim Abrufen der Wünsche:", error);
        // Fallback-Nachricht bei API-Fehler
        wishTextElements[0].textContent = "Verbindung fehlgeschlagen";
        wishUserElements[0].textContent = "";
        if (wishTextElements[1]) {
            wishTextElements[1].textContent = '';
            wishUserElements[1].textContent = '';
        }
    }
}

getWishes();
setInterval(getWishes, 2000); // Intervall leicht erhöht, um die Animation nicht zu überlasten