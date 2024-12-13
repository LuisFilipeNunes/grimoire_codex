from typing import List
import requests
import json
import time
import os
from datetime import datetime

class Deck:
    def __init__(self, deckName : str = "deck"):
        self.cards:List[Card] =[]
        self.name = None
        self.decklist = None
        
        self.deck_size = len(self.cards)
        if deckName:
            self.name = deckName
        elif self.name == None:
            self.name = f"deck-{datetime.now().strftime('%Y-%m-%d-%H-%M-%S')}"


    def populate_deck(self, decklist):
        for card in decklist:
            self.cards.append(Card(card))
        self.deck_size = len(self.cards)

    def get_card_collection(self):
        identifiers = self.__build_identifiers()
        data = self.__json_collector(identifiers)
        self.__link_image_to_card(data)
        self.__download_images()
    
    def __build_identifiers(self) -> json:
        all_identifiers = []
        for card in self.cards:
            if card.collector and card.set_code:
                identifier = {
                    "set": card.set_code,
                    "collector_number": card.collector
                }
            else:
                identifier = {"name": card.name}
                
            all_identifiers.append(identifier)
        print(all_identifiers)
        return all_identifiers
    
    def __json_collector(self, identifier) -> json:
        api_endpoint = "https://api.scryfall.com/cards/collection"
        BATCH_SIZE = 75
        data = []
          # Split into batches of 75
        for i in range(0, len(identifier), BATCH_SIZE):
            batch = identifier[i:i + BATCH_SIZE]
            payload = {"identifiers": batch}
            
            # Send payload here
            response = requests.post(api_endpoint, json=payload, timeout=10)
            data.append(response.json())
            if i + BATCH_SIZE < len(identifier):
                time.sleep(0.5)

        deck_path = self.__build_directory()
        file_path = os.path.join(deck_path, f'{self.name}-json-data.txt')

        with open(file_path, 'w', encoding='utf-8') as file:
            json.dump(data, file, indent=2 )

        return data
    
    def __build_directory(self, cards = 0):

    # Create main deck directory if it doesn't exist
        if not os.path.exists('decks'):
            os.makedirs('decks')
        
        # Create deck-specific directory if it doesn't exist
        deck_path = os.path.join('decks', self.name)
        if not os.path.exists(deck_path):
            os.makedirs(deck_path)
        if cards == 1:
            cardlist = os.path.join(deck_path, "cards")
            if not os.path.exists(cardlist):
                os.makedirs(cardlist)
            return cardlist

        return deck_path
    
    def __link_image_to_card(self, data):
        for response in data:
            for card_data in response['data']:
                card_name = card_data['name']
                png_url = card_data['image_uris']['png']
                set_code = card_data['set']
                collector_number = card_data['collector_number']
                
                for card in self.cards:
                    if card.set_code == None:
                        if card_name == card.name:
                            card.image_url = png_url
                    if card.collector == collector_number and card.set_code.lower() == set_code.lower():
                        card.image_url = png_url
    
    def __download_images(self):
        deck_path = self.__build_directory(cards = 1)
        for card in self.cards:
            print(card.image_url)
            card.get_image(deck_path)


class Card:
    def __init__(self, card: List| None = None) :
        self.quantity = 0
        self.name = None
        self.set_code = None
        self.collector = None
        self.image_url = None
        if card is not None:  
            self.construct_card(card)

    def construct_card(self, card: List):
        self.quantity = card[0]
        self.name = card[1]
        if len(card) > 2:
            self.set_code = card[2]
            self.collector = card[3]

    def get_image(self, deck_path):
        for card in range(1, self.quantity+1):
            image_path = os.path.join(deck_path, f'{self.name}-{card}.png')
            if os.path.exists(image_path):
                image_path = os.path.join(deck_path, f'ALT-{self.name}-{card}.png')
            response = requests.get(self.image_url, timeout=10)
            with open(image_path, 'wb') as file:
                file.write(response.content)

class DeckBox:
    def __init__(self, deck_data: str = None, deck_name: str = None):
        self.cards_data = None
        self.deck = None
        self.decklist = None
        self.deck_name = None
        if deck_data:
            self.cards_data = deck_data  
        if deck_name:
            self.deck_name = deck_name
        

    def __shield_cards(self) -> list:
        deck = []
        cards = self.cards_data.split('\n')
        
        for card in cards:
            if card.strip():  # Check if line is not empty
                quantity, rest = card.strip().split(' ', 1)
                quantity = int(quantity)
                parts = rest.rsplit(' ', 2) 
                
                if len(parts) == 3 and parts[1].isupper():
                    name = parts[0]
                    card_set = parts[1]
                    collector_number = parts[2]
                    deck.append([quantity, name, card_set, collector_number])
                else:
                    deck.append([quantity, rest])
        self.decklist = deck
   
    def build_deck(self):
        self.deck = Deck(self.deck_name)
        self.__shield_cards()
        self.deck.populate_deck(self.decklist)
        self.deck.get_card_collection()
