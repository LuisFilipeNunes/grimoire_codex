from flask import Flask, render_template, jsonify, request
from deck import DeckBox

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

    return jsonify({'status': 'success', 'deck size': deckbox.deck.deck_size})
    
if __name__ == '__main__':
    app.run(debug=True)