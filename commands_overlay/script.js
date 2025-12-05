const API_URL = 'http://127.0.0.1:5000/api/v1/commands';
const POLLING_INTERVAL_MS = 500;
const FADE_OUT_DURATION_MS = 500;

const container = document.getElementById('command-container');
const textElement = document.getElementById('command-text');
const costsElement = document.getElementById('command-costs');

let currentCommandId = null;
let isVisible = false;

async function pollActiveCommand() {
    if (!container) return;

    try {
        const response = await fetch(API_URL + '?t=' + new Date().getTime());
        if (!response.ok) return;

        const command = await response.json();

        // --- NEUER BEFEHL ---
        if (command && command.id && command.id !== currentCommandId) {
            console.log("Command:", command.text);
            currentCommandId = command.id;
            isVisible = true;

            textElement.textContent = command.text;
            costsElement.textContent = `${command.costs} Whieties`;

            // SUPERFAN CHECK
            if (command.is_superfan) {
                container.classList.add('superfan');
            } else {
                container.classList.remove('superfan');
            }

            container.classList.remove('hide');
            container.classList.add('show');
        }
        // --- AUSBLENDEN ---
        else if ((!command || !command.id) && isVisible) {
            isVisible = false;
            currentCommandId = null;

            container.classList.remove('show');
            container.classList.add('hide');

            setTimeout(() => {
                if (!isVisible) {
                     textElement.textContent = "";
                     costsElement.textContent = "";
                     // Reset style
                     container.classList.remove('superfan');
                }
            }, FADE_OUT_DURATION_MS);
        }

    } catch (error) {
        console.error(error);
    }
}

pollActiveCommand();
setInterval(pollActiveCommand, POLLING_INTERVAL_MS);