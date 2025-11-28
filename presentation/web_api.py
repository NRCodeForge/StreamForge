from flask import Flask, jsonify, send_from_directory, request
import os

# Importiere Service Layer (NEUER WEG)
from services.service_provider import (
    wish_service_instance,
    like_service_instance,
    subathon_service_instance,
    command_service_instance # NEU
)

# Importiere Infrastruktur
from config import (
    get_path, BASE_HOST, BASE_PORT, API_ROOT,
    WISHES_ENDPOINT, NEXT_WISH_ENDPOINT, RESET_WISHES_ENDPOINT,
    LIKE_CHALLENGE_ENDPOINT, COMMANDS_ENDPOINT, COMMANDS_TRIGGER_ENDPOINT # NEU
)
from utils import server_log

app = Flask(__name__)

# --- Wishlist API Endpunkte ---
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
        # HINWEIS: Hier war deine Löschlogik. Stelle sicher, dass wish_service_instance.advance_offset() das Löschen korrekt durchführt.
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

# --- Like Challenge API Endpunkt ---
@app.route(LIKE_CHALLENGE_ENDPOINT, methods=['GET'])
def get_like_challenge_data():
    try:
        data = like_service_instance.get_challenge_status()
        return jsonify(data)
    except Exception as e:
        server_log.error(f"Like Challenge Fehler: {e}")
        return jsonify({"error": str(e)}), 500

# --- COMMANDS API (MODIFIZIERT) ---
@app.route(COMMANDS_ENDPOINT, methods=['GET'])
def get_commands_data():
    """API-Endpunkt, der den *aktuell aktiven* Command zurückgibt (aus active.json)."""
    try:
        active_command = command_service_instance.get_active_command()
        return jsonify(active_command)
    except Exception as e:
        server_log.error(f"Fehler beim Abrufen des aktiven Commands: {e}")
        return jsonify({'error': 'Fehler beim Abrufen des aktiven Commands.'}), 500

@app.route(COMMANDS_TRIGGER_ENDPOINT, methods=['POST'])
def trigger_command():
    """(Webhook) Startet die *gesamte* Command-Sequenz."""
    try:
        command_service_instance.trigger_command_loop() # Ruft die Loop-Funktion auf
        return jsonify({'message': 'Command-Sequenz erfolgreich gestartet.'}), 200
    except Exception as e:
        server_log.error(f"Fehler beim Triggern der Command-Sequenz: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/v1/like_challenge/test', methods=['POST'])
def trigger_test_likes():
    try:
        # Füge pauschal z.B. 100 Likes hinzu (oder einen Wert aus dem Request)
        like_service_instance.add_test_likes(100)
        return jsonify({'message': '100 Test-Likes hinzugefügt.'}), 200
    except Exception as e:
        server_log.error(f"Test-Like Fehler: {e}")
        return jsonify({'error': str(e)}), 500

# --- Statische Datei-Endpunkte (unverändert) ---

@app.route('/like_progress_bar/<path:path>')
def serve_like_progress_bar(path):
    directory = get_path('like_progress_bar')
    return send_from_directory(directory, path)
@app.route('/killer_wishes/<path:path>')
def serve_killer_wishes(path):
    directory = get_path('killer_wishes')
    return send_from_directory(directory, path)

@app.route('/timer_overlay/<path:path>')
def timer_overlay_index(path):
    directory = get_path('timer_overlay')
    return send_from_directory(directory, path)

@app.route('/subathon_overlay/<path:path>')
def serve_subathon_overlay(path):
    directory = get_path('subathon_overlay')
    return send_from_directory(directory, path)

@app.route('/like_overlay/<path:path>')
def serve_like_overlay(path):
    directory = get_path('like_overlay')
    return send_from_directory(directory, path)

# NEU: Route für /commands/
@app.route('/commands/<path:path>')
def serve_commands_overlay(path):
    directory = get_path('commands_overlay')
    return send_from_directory(directory, path)