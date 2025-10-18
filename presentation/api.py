from flask import Flask, jsonify, send_from_directory, request
import os

# Importiere Service Layer
from services.wish_service import WishService
from services.like_challenge_service import LikeChallengeService
# Importiere Infrastruktur
from config import get_path, BASE_HOST, BASE_PORT, API_ROOT, WISHES_ENDPOINT, NEXT_WISH_ENDPOINT, RESET_WISHES_ENDPOINT, LIKE_CHALLENGE_ENDPOINT
from utils import server_log

app = Flask(__name__)
wish_service = WishService()
like_service = LikeChallengeService()


# --- Wishlist API Endpunkte ---

@app.route(WISHES_ENDPOINT, methods=['GET'])
def get_killer_wishes_data():
    """API-Endpunkt für die Anzeige von 2 Wünschen mit aktuellem Offset."""
    try:
        wuensche = wish_service.get_current_wishes()
        return jsonify(wuensche)
    except Exception as e:
        server_log.error(f"Fehler beim Abrufen der Wünsche: {e}")
        return jsonify({'error': 'Fehler beim Abrufen der Wünsche.'}), 500

@app.route(NEXT_WISH_ENDPOINT, methods=['POST'])
def next_killer():
    """API-Endpunkt für den Hotkey, um den nächsten Wunsch anzuzeigen."""
    try:
        new_offset = wish_service.advance_offset()
        return jsonify({'message': 'Offset aktualisiert', 'new_offset': new_offset})
    except Exception as e:
        server_log.error(f"Fehler beim Weiterschalten des Offsets: {e}")
        return jsonify({'error': 'Fehler beim Aktualisieren des Offsets.'}), 500

@app.route(RESET_WISHES_ENDPOINT, methods=['POST'])
def reset_database():
    """API-Endpunkt zum Zurücksetzen der Datenbank."""
    try:
        wish_service.reset_wishes()
        return jsonify({'message': 'Datenbank erfolgreich zurückgesetzt.'}), 200
    except Exception as e:
        server_log.error(f"Datenbank-Fehler beim Zurücksetzen: {e}")
        return jsonify({'error': 'Fehler beim Zurücksetzen der Datenbank.'}), 500

@app.route(WISHES_ENDPOINT, methods=['POST'])
def add_killerwunsch():
    """API-Endpunkt zum Hinzufügen von Wünschen."""
    if not request.json or 'wunsch' not in request.json or 'user_name' not in request.json:
        server_log.error('Fehler: Falsches Format beim Hinzufügen eines Wunsches.')
        return jsonify({'error': 'Falsches Format, "wunsch" oder "user_name" fehlt.'}), 400

    wunsch = request.json['wunsch']
    user_name = request.json['user_name']

    try:
        wish_service.add_new_wish(wunsch, user_name)
        return jsonify({'message': 'Wunsch erfolgreich hinzugefügt.'}), 201
    except Exception as e:
        server_log.error(f'Datenbank-Fehler beim Hinzufügen des Wunsches: {e}')
        return jsonify({'error': 'Fehler beim Hinzufügen des Wunsches.'}), 500

# --- Like Challenge API Endpunkt ---

@app.route(LIKE_CHALLENGE_ENDPOINT, methods=['GET'])
def get_like_challenge_data():
    """API-Endpunkt für die Live-Daten der Like Challenge."""
    try:
        data = like_service.get_challenge_status()
        return jsonify(data)
    except Exception as e:
        server_log.error(f"Like Challenge Fehler: {e}")
        return jsonify({"error": str(e)}), 500


# --- Statische Datei-Endpunkte (unverändert) ---

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


if __name__ == '__main__':
    # Nur zum direkten Testen, Hauptstartpunkt ist main.py
    app.run(host=BASE_HOST, port=BASE_PORT, debug=False, use_reloader=False)