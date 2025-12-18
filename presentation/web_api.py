from flask import Flask, jsonify, send_from_directory, request, render_template_string
import os
import requests

# Importiere Service Layer
from services.service_provider import (
    wish_service_instance,
    like_service_instance,
    subathon_service_instance,
    command_service_instance,
    twitch_service_instance,
    wheel_service_instance
)

# Importiere Infrastruktur
# WICHTIG: get_persistent_path hinzugefügt!
from config import (
    get_path, get_persistent_path, BASE_HOST, BASE_PORT, API_ROOT,
    WISHES_ENDPOINT, NEXT_WISH_ENDPOINT, RESET_WISHES_ENDPOINT,
    LIKE_CHALLENGE_ENDPOINT, COMMANDS_ENDPOINT, COMMANDS_TRIGGER_ENDPOINT
)
from utils import server_log

app = Flask(__name__)


# --- HILFSFUNKTION FÜR OVERLAYS ---
def serve_overlay_file(folder_name, filename):
    """
    Sucht die Datei erst im Benutzer-Ordner (gespeicherte Settings),
    und falls dort nicht vorhanden, im Programm-Ordner (Originale).
    """
    # 1. Suche im externen/persistenten Ordner (wo deine Settings gespeichert werden)
    persistent_dir = get_persistent_path(folder_name)
    if os.path.exists(os.path.join(persistent_dir, filename)):
        return send_from_directory(persistent_dir, filename)

    # 2. Fallback: Nimm die Datei aus dem internen Programm-Ordner (Assets)
    bundled_dir = get_path(folder_name)
    return send_from_directory(bundled_dir, filename)


# --- TWITCH AUTH CALLBACK ---
@app.route('/auth/twitch/callback')
def twitch_callback():
    return render_template_string("""
    <html>
        <head>
            <title>Authorizing...</title>
            <style>body { font-family: sans-serif; background: #1a1a1a; color: white; text-align: center; padding-top: 50px; }</style>
        </head>
        <body>
            <h1>StreamForge: Authorizing...</h1>
            <p id="status">Verarbeite Token...</p>
            <script>
                const hash = window.location.hash.substring(1); 
                const params = new URLSearchParams(hash);
                const token = params.get('access_token');

                if (token) {
                    document.getElementById("status").innerText = "Token gefunden, speichere...";
                    fetch('/api/v1/auth/twitch/save', {
                        method: 'POST',
                        headers: {'Content-Type': 'application/json'},
                        body: JSON.stringify({access_token: token})
                    }).then(res => res.json()).then(data => {
                        if(data.status === "ok") {
                            document.body.innerHTML = "<h1>✅ Erfolgreich verbunden!</h1><p>Verbunden als: " + data.user + "</p><p>Du kannst dieses Fenster schließen.</p>";
                        } else {
                            document.body.innerHTML = "<h1>❌ Fehler beim Speichern.</h1><p>" + (data.message || "Unbekannter Fehler") + "</p>";
                        }
                    }).catch(err => {
                        document.body.innerHTML = "<h1>❌ Netzwerkfehler.</h1><p>" + err + "</p>";
                    });
                } else {
                    document.body.innerHTML = "<h1>❌ Kein Token gefunden.</h1><p>Bitte versuche den Login erneut.</p>";
                }
            </script>
        </body>
    </html>
    """)


@app.route('/api/v1/auth/twitch/save', methods=['POST'])
def save_twitch_token():
    data = request.json
    token = data.get('access_token')

    if token:
        settings = twitch_service_instance.get_settings()
        client_id = settings.get("twitch_client_id", "")

        if not client_id:
            server_log.warning("Twitch Client ID fehlt in den Einstellungen!")

        headers = {
            "Authorization": f"Bearer {token}",
            "Client-Id": client_id
        }
        try:
            r = requests.get("https://api.twitch.tv/helix/users", headers=headers)

            if r.status_code == 200:
                user_data = r.json()['data'][0]
                username = user_data['login']

                settings["twitch_token"] = token
                settings["twitch_username"] = username
                twitch_service_instance.save_settings(settings)
                twitch_service_instance.update_credentials(username, token)

                server_log.info(f"Twitch Login erfolgreich: {username}")
                return jsonify({"status": "ok", "user": username})
            else:
                server_log.error(f"Twitch API Fehler ({r.status_code}): {r.text}")
                return jsonify(
                    {"status": "error", "message": "Twitch Validierung fehlgeschlagen. Client-ID korrekt?"}), 400
        except Exception as e:
            server_log.error(f"Twitch Validation Error: {e}")
            return jsonify({"status": "error", "message": str(e)}), 500

    return jsonify({"status": "error", "message": "Kein Token"}), 400


# --- Wishlist API ---
@app.route(WISHES_ENDPOINT, methods=['GET'])
def get_killer_wishes_data():
    try:
        wuensche = wish_service_instance.get_current_wishes()
        return jsonify(wuensche)
    except Exception as e:
        server_log.error(f"Fehler beim Abrufen der Wünsche: {e}")
        return jsonify({'error': 'Fehler beim Abrufen der Wünsche.'}), 500


@app.route(NEXT_WISH_ENDPOINT, methods=['POST'])
def next_killer():
    try:
        new_offset = wish_service_instance.advance_offset()
        return jsonify({'message': 'Offset aktualisiert', 'new_offset': new_offset})
    except Exception as e:
        server_log.error(f"Fehler beim Weiterschalten des Offsets: {e}")
        return jsonify({'error': 'Fehler beim Aktualisieren des Offsets.'}), 500


@app.route(RESET_WISHES_ENDPOINT, methods=['POST'])
def reset_database():
    try:
        wish_service_instance.reset_wishes()
        return jsonify({'message': 'Datenbank erfolgreich zurückgesetzt.'}), 200
    except Exception as e:
        server_log.error(f"Datenbank-Fehler beim Zurücksetzen: {e}")
        return jsonify({'error': 'Fehler beim Zurücksetzen der Datenbank.'}), 500


@app.route(WISHES_ENDPOINT, methods=['POST'])
def add_killerwunsch():
    if not request.json or 'wunsch' not in request.json or 'user_name' not in request.json:
        server_log.error('Fehler: Falsches Format beim Hinzufügen eines Wunsches.')
        return jsonify({'error': 'Falsches Format, "wunsch" oder "user_name" fehlt.'}), 400
    wunsch = request.json['wunsch']
    user_name = request.json['user_name']
    try:
        wish_service_instance.add_new_wish(wunsch, user_name)
        return jsonify({'message': 'Wunsch erfolgreich hinzugefügt.'}), 201
    except Exception as e:
        server_log.error(f'Datenbank-Fehler beim Hinzufügen des Wunsches: {e}')
        return jsonify({'error': 'Fehler beim Hinzufügen des Wunsches.'}), 500


@app.route('/api/v1/wishes/check_place', methods=['POST'])
def trigger_place_check():
    if not request.json or 'user_name' not in request.json:
        return jsonify({'error': 'user_name fehlt'}), 400

    user_name = request.json['user_name']
    place = wish_service_instance.check_user_place(user_name)

    if place:
        return jsonify({'message': f'User {user_name} ist auf Platz {place}', 'place': place})
    else:
        return jsonify({'message': 'User nicht gefunden', 'place': -1}), 404


# --- Like Challenge API ---
@app.route(LIKE_CHALLENGE_ENDPOINT, methods=['GET'])
def get_like_challenge_data():
    try:
        data = like_service_instance.get_challenge_status()
        return jsonify(data)
    except Exception as e:
        server_log.error(f"Like Challenge Fehler: {e}")
        return jsonify({"error": str(e)}), 500


# --- COMMANDS API ---
@app.route(COMMANDS_ENDPOINT, methods=['GET'])
def get_commands_data():
    try:
        active_command = command_service_instance.get_active_command()
        return jsonify(active_command)
    except Exception as e:
        server_log.error(f"Fehler beim Abrufen des aktiven Commands: {e}")
        return jsonify({'error': 'Fehler beim Abrufen des aktiven Commands.'}), 500


@app.route(COMMANDS_TRIGGER_ENDPOINT, methods=['POST'])
def trigger_command():
    try:
        command_service_instance.trigger_command_loop()
        return jsonify({'message': 'Command-Sequenz erfolgreich gestartet.'}), 200
    except Exception as e:
        server_log.error(f"Fehler beim Triggern der Command-Sequenz: {e}")
        return jsonify({'error': str(e)}), 500


# --- SUBATHON & GAMBIT API ---
@app.route('/api/v1/events/gambler/next', methods=['GET'])
def get_next_gambit():
    event = subathon_service_instance.pop_next_gambit_event()
    if event:
        return jsonify(event)
    else:
        return jsonify({})


@app.route('/api/v1/gambit/options', methods=['GET'])
def get_gambit_options():
    try:
        options = subathon_service_instance.get_gambit_options()
        texts = [o.get("text", "???") for o in options]
        return jsonify(texts)
    except:
        return jsonify([])


@app.route('/api/v1/timer/streamerbot', methods=['POST'])
def trigger_streamerbot_event():
    if not request.json:
        return jsonify({'error': 'JSON Body fehlt'}), 400
    try:
        subathon_service_instance.handle_streamerbot_event(request.json)
        return jsonify({'message': 'Event verarbeitet'}), 200
    except Exception as e:
        server_log.error(f"Streamerbot API Fehler: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/v1/timer/control', methods=['POST'])
def timer_control():
    if not request.json or 'action' not in request.json:
        return jsonify({'error': 'Action fehlt'}), 400
    action = request.json['action']
    if action == "start":
        subathon_service_instance.set_paused(False)
    elif action == "pause":
        subathon_service_instance.set_paused(True)
    elif action == "reset":
        subathon_service_instance.reset_timer()
    return jsonify({'message': f'Timer {action} ausgeführt'}), 200


@app.route('/api/v1/timer/state', methods=['GET'])
def get_timer_state():
    return jsonify(subathon_service_instance.get_state())


@app.route('/api/v1/like_challenge/test', methods=['POST'])
def trigger_test_likes():
    try:
        like_service_instance.add_test_likes(100)
        return jsonify({'message': '100 Test-Likes hinzugefügt.'}), 200
    except Exception as e:
        server_log.error(f"Test-Like Fehler: {e}")
        return jsonify({'error': str(e)}), 500


# --- EVENTS ---
@app.route('/api/v1/events/time_warp', methods=['POST'])
def trigger_time_warp():
    subathon_service_instance.trigger_time_warp(60)
    return jsonify({'message': 'Time Warp gestartet'}), 200


@app.route('/api/v1/events/blackout', methods=['POST'])
def trigger_blackout():
    subathon_service_instance.trigger_blackout(120)
    return jsonify({'message': 'Blackout gestartet'}), 200


@app.route('/api/v1/events/gambler', methods=['POST'])
def trigger_gambler():
    result = subathon_service_instance.trigger_gambler()
    return jsonify({'message': f'Gambler Ergebnis: {result}'}), 200


@app.route('/api/v1/events/freezer', methods=['POST'])
def trigger_freezer():
    subathon_service_instance.trigger_freezer(180)
    return jsonify({'message': 'Freezer gestartet'}), 200


@app.route('/api/v1/wheel/state', methods=['GET'])
def get_wheel_state():
    state = wheel_service_instance.get_current_state()
    if state:
        return jsonify(state)
    return jsonify({})  # Leeres JSON wenn inaktiv


# --- STATISCHE DATEIEN (OVERLAYS) ---
# Hier nutzen wir jetzt die clevere Funktion 'serve_overlay_file',
# die erst nach gespeicherten Dateien sucht.

@app.route('/wheel_overlay/<path:path>')
def serve_wheel_overlay(path):
    return serve_overlay_file('wheel_overlay', path)


@app.route('/like_progress_bar/<path:path>')
def serve_like_progress_bar(path):
    return serve_overlay_file('like_progress_bar', path)


@app.route('/killer_wishes/<path:path>')
def serve_killer_wishes(path):
    return serve_overlay_file('killer_wishes', path)


@app.route('/timer_overlay/<path:path>')
def timer_overlay_index(path):
    return serve_overlay_file('timer_overlay', path)


@app.route('/subathon_overlay/<path:path>')
def serve_subathon_overlay(path):
    # Das fixt dein Problem mit dem Subathon Trigger!
    return serve_overlay_file('subathon_overlay', path)


@app.route('/like_overlay/<path:path>')
def serve_like_overlay(path):
    return serve_overlay_file('like_overlay', path)


@app.route('/commands/<path:path>')
def serve_commands_overlay(path):
    return serve_overlay_file('commands_overlay', path)


@app.route('/place_overlay/<path:path>')
def serve_place_overlay(path):
    return serve_overlay_file('place_overlay', path)


@app.route('/gambler_overlay/<path:path>')
def serve_gambler_overlay(path):
    return serve_overlay_file('gambler_overlay', path)