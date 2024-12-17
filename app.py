from flask import Flask, render_template, jsonify, request, send_file
from deck import DeckBox
import os
import shutil


app = Flask(__name__)

@app.route('/')
@app.route('/index')
def index():
    return render_template('index.html')

@app.route('/search_decklist', methods=['POST'])
def search_decklist():
    deck_data = request.form['decklist']
    deck_name = request.form['deckName']
    deckbox = DeckBox(deck_data, deck_name)
    deckbox.build_deck()

    return jsonify({'status': 'success', 'message': 'Deck created successfully'})

@app.route('/ready_decks')
def ready_decks():
    if not os.path.exists('decks'):
        return render_template('ready_decks.html', decks="Let's create your first deck!")
    
    deck_files = []
    for file in os.listdir('decks'):
        if file.endswith('.zip'):
            deck_files.append(file)
            
    if not deck_files:
        return render_template('ready_decks.html', decks="Let's create your first deck!")
        
    return render_template('ready_decks.html', decks=deck_files)

@app.route('/download_deck/<filename>')
def download_deck(filename):
    deck_path = os.path.join('decks', filename)
    return send_file(
        deck_path,
        mimetype='application/zip',
        as_attachment=True,
        download_name=filename
    )

@app.route('/clean_folder',  methods=['POST'])
def clean_folder():
    folder_path = 'decks'
    # First remove files
    for filename in os.listdir(folder_path):
        file_path = os.path.join(folder_path, filename)
        try:
            if os.path.isfile(file_path):
                os.remove(file_path)
            elif os.path.isdir(file_path):
                shutil.rmtree(file_path)           
        except Exception as e:
            print(f"Error deleting {file_path}: {e}")
    
    return jsonify({"message": "Folder cleaned successfully"})


@app.route('/help')
def help():
    return render_template('help.html')


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000, debug=True)