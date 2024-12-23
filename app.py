from flask import Flask, render_template, jsonify, request, send_file
from werkzeug.exceptions import BadRequest
from requests.exceptions import RequestException
from json.decoder import JSONDecodeError
from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime, timedelta
from deck import DeckBox, Deck
import os
import shutil
from config import (
    DECK_FOLDER,
    CLEANUP_THRESHOLD_MINUTES,
    SCHEDULER_INTERVAL_MINUTES,
    HOST,
    PORT,
    DEBUG
)

app = Flask(__name__)

@app.route('/')
@app.route('/index')
def index():
    return render_template('index.html')

@app.route('/search_decklist', methods=['POST'])
def search_decklist():
    try:
        deck_data = request.form['decklist']
        deck_name = request.form['deckName'].strip()
        
        # Validate deck data
        if not deck_data:
            return jsonify({'status': 'error', 'message': 'Decklist cannot be empty'}), 400
        deckbox = DeckBox(deck_data, deck_name)
        deckbox.build_deck()
        return jsonify({'status': 'success', 'message': 'Deck created successfully'})
    
    except BadRequest as e:
        return jsonify({'status': 'error', 'message': 'Invalid request data: ' + str(e)}), 400
    except RequestException as e:
        return jsonify({'status': 'error', 'message': 'Failed to fetch card data from API: ' + str(e)}), 503
    except JSONDecodeError as e:
        return jsonify({'status': 'error', 'message': 'Invalid JSON response from API: '+ str(e)}), 502
    except OSError as e:
        return jsonify({'status': 'error', 'message': 'File system operation failed: '+ str(e)}), 500
    except ValueError as e:
        return jsonify({'status': 'error', 'message': str(e)}), 400

@app.route('/ready_decks')
def ready_decks():
    if not os.path.exists(DECK_FOLDER):
        return render_template('ready_decks.html', decks="Let's create your first deck!")
    
    deck_files = []
    for file in os.listdir(DECK_FOLDER):
        if file.endswith('.zip'):
            deck_files.append(file)
            
    if not deck_files:
        return render_template('ready_decks.html', decks="Let's create your first deck!")
        
    return render_template('ready_decks.html', decks=deck_files)

@app.route('/download_deck/<filename>')
def download_deck(filename):
    deck_path = os.path.join(DECK_FOLDER, filename)
    if not os.path.exists(deck_path):
        return jsonify({'error': 'File not found'}), 404
    return send_file(
        deck_path,
        mimetype='application/zip',
        as_attachment=True,
        download_name=filename
    )

@app.route('/clean_folder',  methods=['POST'])
def clean_folder():
    folder_path = 'decks'
    try:
        for filename in os.listdir(folder_path):
            file_path = os.path.join(folder_path, filename)
            if os.path.isfile(file_path):
                os.remove(file_path)
            elif os.path.isdir(file_path):
                shutil.rmtree(file_path)           
        return jsonify({"message": "Folder cleaned successfully"})
        
    except FileNotFoundError:
        return jsonify({"status": "error", "message": f"Folder not found: {folder_path}"}), 404
    except PermissionError as e:
        return jsonify({"status": "error", "message": f"Permission denied when cleaning folder: {str(e)}"}), 403
    except OSError as e:
        return jsonify({"status": "error", "message": f"System error while cleaning folder: {str(e)}"}), 500

@app.route('/help')
def help_page() -> str:
    """Render the help page with instructions and documentation for users."""
    return render_template('help.html')

def cleanup_old_files():
    threshold = datetime.now() - timedelta(minutes=CLEANUP_THRESHOLD_MINUTES)
    
    for filename in os.listdir(DECK_FOLDER):
        file_path = os.path.join(DECK_FOLDER, filename)
        if os.path.isfile(file_path):
            file_time = datetime.fromtimestamp(os.path.getctime(file_path))
            if file_time < threshold:
                os.remove(file_path)

scheduler = BackgroundScheduler()
scheduler.add_job(func=cleanup_old_files, trigger="interval", minutes=SCHEDULER_INTERVAL_MINUTES)
scheduler.start()

if __name__ == '__main__':
    app.run(host=HOST, port=PORT, debug=DEBUG)