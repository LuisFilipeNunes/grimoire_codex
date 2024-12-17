from typing import List
import requests
import json
import time
import os
import zipfile
import shutil
from datetime import datetime

class Deck:
    # Main class to handle deck operations and card management
    def __init__(self, deckName : str = "deck"):
        self.cards:List[Card] =[]
        self.name = None
        self.decklist = None
        self.card_error = 0
        self.json_data_path = None
        self.deck_size = 0

        # Set deck name or generate timestamp-based name if none provided
        if deckName:
            self.name = deckName
        elif self.name == None:
            self.name = f"deck-{datetime.now().strftime('%Y-%m-%d-%H-%M-%S')}"

    def populate_deck(self, decklist):
        # Creates Card objects from decklist and adds them to the deck
        for card in decklist:
            self.cards.append(Card(card))

        self.deck_size = sum(card.quantity for card in self.cards)

    def get_card_collection(self):
        # Main method to fetch card data and images from Scryfall API
        identifiers = self.__build_identifiers()
        data = self.__json_collector(identifiers)
        self.__link_image_to_card(data)
        self.__construct_data_file()
        self.__check_not_found()
        self.__download_images()
   
    def __build_identifiers(self) -> json:
        # Builds API request identifiers based on card info
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
        #print(all_identifiers)
        return all_identifiers
    
    def __json_collector(self, identifier) -> json:
        api_endpoint = "https://api.scryfall.com/cards/collection"
        BATCH_SIZE = 75
        data = []
          # Split into batches of 75, as asked by the API
        for i in range(0, len(identifier), BATCH_SIZE):
            batch = identifier[i:i + BATCH_SIZE]
            payload = {"identifiers": batch}
            
            # Send payload here
            response = requests.post(api_endpoint, json=payload, timeout=10)
            data.append(response.json())
            if i + BATCH_SIZE < len(identifier):
                time.sleep(0.5)

        deck_path = self.build_directory()
        file_path = os.path.join(deck_path, f'{self.name}-json-data.txt')
        self.json_data_path = file_path
        with open(file_path, 'w', encoding='utf-8') as file:
            json.dump(data, file, indent=2 )

        return data
    
    def build_directory(self, signal = 0):
        if not os.path.exists('decks'):
            os.makedirs('decks')

        deck_path = os.path.join('decks', self.name)

        if not os.path.exists(deck_path):
            os.makedirs(deck_path)

        if signal == 1:
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
                print("##############",card_name, png_url, set_code, collector_number)
                
                for card in self.cards:
                    if card.set_code == None:
                        if card_name == card.name:
                            card.image_url = png_url
                    if card.collector == collector_number and card.set_code.lower() == set_code.lower():
                        card.image_url = png_url

    def __download_images(self):
        deck_path = self.build_directory(signal = 1)
        for card in self.cards:
            #print(card.image_url)
            if card.image_url:
                card.get_image(deck_path)

            elif card.image_url == None:
                self.__log_error()
                self.__addendum_info(f"Card {card.name}, with the set {card.set_code} and collector's number: {card.collector} does not have a valid image URL. Its probably the wrong set code or collector number.")

    def __construct_data_file(self):
        file_path = os.path.join(self.build_directory(), "deck-info.txt")
        with open(file_path, 'w', encoding='utf-8') as file:
            file.write(f"Deck Name: {self.name}\n")
            file.write(f"Deck Size: {self.deck_size}\n")
            file.write("Decklist: \n")
            
        for card in self.cards:
            with open(file_path, 'a', encoding='utf-8') as file:
                file.write(f"{card.quantity} {card.name} {card.set_code or ''} {card.collector or ''}\n")
    
    def __check_not_found(self):
        with open(self.json_data_path, 'r', encoding='utf-8') as file:
            data = json.load(file)
        
        not_found_cards = []
        for response in data:
            if 'not_found' in response:
                not_found_cards.extend(response['not_found'])
                
        if not_found_cards:
            self.__log_error()
            self.__addendum_info("Cards not found in Scryfall database:\n")
            for card in not_found_cards:
                if 'set' in card and 'collector_number' in card:
                    self.__addendum_info(f"Set: {card['set']}, Collector Number: {card['collector_number']}\n")
                elif 'name' in card:
                    self.__addendum_info(f"Card Name: {card['name']}\n")

    def __addendum_info(self, text):
        file_path = os.path.join(self.build_directory(), "deck-info.txt")
        with open(file_path, 'a', encoding='utf-8') as file:
            file.write(text)

    def __log_error(self):
        if self.card_error == 0:
            self.__addendum_info("###### ERRORS #######\n")
            self.card_error = 1
            self.__log_error()
        elif self.card_error > 0:
            self.__addendum_info(f"Error #{self.card_error}:\n")
            self.card_error += 1

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
        print(self.zip_deck())

    def zip_deck(self):
        """Creates a zip file of the deck directory"""
        deck_path = self.deck.build_directory()
        zip_path = os.path.join('decks', f'{self.deck.name}.zip')
        
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for root, dirs, files in os.walk(deck_path):
                for file in files:
                    file_path = os.path.join(root, file)
                    arcname = os.path.relpath(file_path, 'decks')
                    zipf.write(file_path, arcname)
        
        return zip_path