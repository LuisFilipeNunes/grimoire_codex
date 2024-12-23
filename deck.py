from typing import List, Dict, Optional, Union, Any, Set, Tuple
import requests
import json
import time
import os
import zipfile
from datetime import datetime

class Deck:
    # Main class to handle deck operations and card management
    def __init__(self, deckName : str = "deck") -> None:
        self.cards:List[Card] =[]
        self.name: Optional[str] = None
        self.decklist: Optional[List[Any]] = None
        self.card_error: int = 0
        self.json_data_path: Optional[str] = None
        self.deck_size: int = 0

        # Set deck name or generate timestamp-based name if none provided
        if deckName and self.validate_deck_name(deckName):
            self.name = deckName
        elif self.name == None:
            self.name = f"deck-{datetime.now().strftime('%Y-%m-%d-%H-%M-%S')}"

    def populate_deck(self, decklist: List[List[Any]]) -> None:
        # Creates Card objects from decklist and adds them to the deck
        for card in decklist:
            self.cards.append(Card(card))

        self.deck_size = sum(card.quantity for card in self.cards)

    def get_card_collection(self):
        # Main method to fetch card data and images from Scryfall API
        identifiers = self.__build_identifiers()
        data = self.__json_collector(identifiers)
        self.__card_constructor_by_json(data)
        self.__construct_data_file()
        self.__check_not_found()
        self.__download_images()
   
    def __build_identifiers(self) ->  List[Dict[str, str]]:
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

        return all_identifiers
    
    def __json_collector(self, identifier: List[Dict[str, str]]) -> List[Dict[str, Any]]:
        # Returns JSON response data
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
    
    def build_directory(self, signal:int = 0) -> str:
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
    
    def __card_constructor_by_json(self, data: List[Dict[str, Any]]) -> None:
        cards_to_remove: Set[Card] = set()
        for response in data:
            # If response has a 'data' key, iterate over its items
            if 'data' in response:
                card_list = response['data']
            else:
                # Handle flat JSON structure
                card_list = [response]

            for card_data in card_list:                    
                card_name = card_data['name']
                set_code = card_data['set']
                collector_number = card_data['collector_number']
                
                # Check for image_uris directly
                if 'image_uris' in card_data:
                    png_url = card_data['image_uris']['png']
                    
                    # Link to the card objects
                    for card in self.cards:
                        if card.set_code is None and card.name.lower() in card_name.lower():
                            card.image_url = png_url
                        if card.collector == collector_number and card.set_code.lower() == set_code.lower():
                            card.image_url = png_url

                # Handle cards with 'card_faces'
                elif 'card_faces' in card_data:
                    for face in card_data['card_faces']:
                        face_name = face['name']
                        png_url = face['image_uris']['png']

                        if not self.multiface_check(face) and (card_data['layout'] == 'transform' or card_data['layout'] == 'modal_dfc'):
                            self.multiface_handler(card_name, face_name)

                        if card_data['layout'] == 'reversible_card' and not self.multiface_check(card_data):
                            for card in self.cards:
                                if card.name.lower() == face_name.lower():
                                    cards_to_remove.add(card) 
                            self.reversible_handler(card_name, face_name = face["flavor_name"], png_url = png_url)
                        #if card_data['layout'] = 'meld':
                            
                        for card in self.cards:
                            if card.is_reversible():
                                pass
                            elif card.set_code is None and card.name.lower() == face_name.lower():
                                card.image_url = png_url
                            elif card.collector == collector_number and card.set_code.lower() == set_code.lower():
                                card.image_url = png_url

        for card in cards_to_remove:
            self.cards.remove(card)

        self.deck_size = sum(card.quantity for card in self.cards)

    def multiface_check(self, card_data):
        face_name = card_data['name']
        if face_name in [card.name for card in self.cards]:
            return True
        return False
    
    def multiface_handler(self, card_name, face_name ):
        new_card = []
        new_card.extend([self.get_card_quantity(card_name),  face_name])
        if self.get_card_set_collection(card_name):
            set_code, collector_number = self.get_card_set_collection(card_name)
            new_card.extend([set_code, collector_number])
        self.cards.append(Card(new_card))

    def reversible_handler(self, card_name, face_name, png_url ):
        new_card = []
        new_card.extend([self.get_card_quantity(card_name),  f"REV-1-{face_name}"])
        if self.get_card_set_collection(card_name):
            set_code, collector_number = self.get_card_set_collection(card_name)
            new_card.extend([set_code, collector_number])
        self.cards.append(Card(new_card, url = png_url))
        
    def __download_images(self):
        deck_path = self.build_directory(signal = 1)
        for card in self.cards:
            if card.image_url:
                card.get_image(deck_path)

            elif card.image_url == None:
                self.__log_error()
                error_message = f"Card {card.name}"
                if card.set_code:
                    error_message += f", with the set {card.set_code}"
                if card.collector:
                    error_message += f" and collector's number: {card.collector}"
                error_message += " does not have a valid image URL."
                self.__addendum_info(error_message + "\n")
    
    def __construct_data_file(self):
        file_path = os.path.join(self.build_directory(), "deck-info.txt")
        with open(file_path, 'w', encoding='utf-8') as file:
            file.write(f"Deck Name: {self.name}\n")
            file.write(f"Deck Size: {self.deck_size}\n")
            file.write("Decklist: \n")
            
        for card in self.cards:
            with open(file_path, 'a', encoding='utf-8') as file:
                file.write(f"{card.quantity} {card.name} {card.set_code or ''} {card.collector or ''} {card.image_url}\n")
    
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
    
    def validate_deck_name(self, name: str) -> bool:
        # Reject empty or whitespace-only names
        if not name or name.isspace():
            return False
        
        # Remove invalid filesystem characters
        invalid_chars = '<>:"/\\|?*'
        if any(char in name for char in invalid_chars):
            return False
        
        # Limit length (example: 50 characters)
        if len(name) > 50:
            return False
            
        return True

    def get_card_quantity(self, card_name):

        for card in self.cards:
            if self.match_card_name(card.name, card_name):
                return card.quantity
            
        return 0
    
    def get_card_set_collection(self, card_name: str, info: Optional[Any] = None) -> Optional[Tuple[str, str]]:
        # Returns tuple of set_code and collector number or None
        for card in self.cards:
            if self.match_card_name(card.name, card_name):
                return card.set_code, card.collector
        return None
    
    def match_card_name(self, card_name: str, full_name: str) -> bool:
        # Returns boolean for name match
        if " // " in full_name:
            first_face_name = full_name.split(" // ")[0]
            return card_name.lower() == first_face_name.lower()
        return card_name.lower() == full_name.lower()

class Card:
    def __init__(self, card: Optional[List[Any]] = None, url: Optional[str] = None) -> None:
        self.quantity: int = 0
        self.name: Optional[str] = None
        self.set_code: Optional[str] = None
        self.collector: Optional[str] = None
        self.image_url: Optional[str] = None
        if card is not None:  
            self.construct_card(card, url)


    def construct_card(self, card: List[Any], url: Optional[str] = None) -> None:
        # Constructs card attributes
        self.quantity = card[0]
        self.name = card[1]
        if len(card) > 2:
            self.set_code = card[2]
            self.collector = card[3]
        if url:
            self.image_url = url

    def get_image(self, deck_path: str) -> None:
        for card in range(1, self.quantity+1):
            image_path = os.path.join(deck_path, f'{self.name}-{card}.png')
            if os.path.exists(image_path):
                image_path = os.path.join(deck_path, f'ALT-{self.name}-{card}.png')
            response = requests.get(self.image_url, timeout=10)
            with open(image_path, 'wb') as file:
                file.write(response.content)

    def is_reversible(self) -> bool:
        return self.name.startswith("REV-1-") if self.name else False

class DeckBox:
    def __init__(self, deck_data: Optional[str] = None, deck_name: Optional[str] = None) -> None:
        self.cards_data: Optional[str] = None
        self.deck: Optional[Deck] = None
        self.decklist: Optional[List[Any]] = None
        self.deck_name: Optional[str] = None
        if deck_data:
            self.cards_data = deck_data  
        if deck_name:
            self.deck_name = deck_name
        

    def __shield_cards(self) -> List[List[Any]]:
        # Returns processed deck list
        deck = []
        cards = self.cards_data.split('\n')
        
        for card in cards:
            if card.strip():  # Check if line is not empty
                quantity, rest = card.strip().split(' ', 1)
                quantity = int(quantity)
                
                # First check for // and get everything before it
                if '//' in rest:
                    name = rest.split('//')[0].strip()
                    remaining = rest.split('//')[1].strip()
                    
                    # Check remaining part for set code and collector number
                    parts = remaining.rsplit(' ', 2)
                    if len(parts) == 3 and parts[1].isupper() and len(parts[1]) == 3:
                        card_set = parts[1]
                        collector_number = parts[2]
                        deck.append([quantity, name, card_set, collector_number])
                    else:
                        deck.append([quantity, name])
                else:
                    # then, do  the same for the rest
                    parts = rest.rsplit(' ', 2)
                    if len(parts) == 3 and parts[1].isupper():
                        name = parts[0]
                        card_set = parts[1]
                        collector_number = parts[2]
                        deck.append([quantity, name, card_set, collector_number])
                    else:
                        deck.append([quantity, rest])
                        
        self.decklist = deck

   
    def build_deck(self) -> None:
        self.deck = Deck(self.deck_name)
        self.__shield_cards()
        self.deck.populate_deck(self.decklist)
        self.deck.get_card_collection()
        print(self.zip_deck())

    def zip_deck(self) -> str:
        """Creates a zip file of the deck directory"""
        deck_path = self.deck.build_directory()
        zip_path = os.path.join('decks', f'{self.deck.name}.zip')
        
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for root, _, files in os.walk(deck_path):
                for file in files:
                    file_path = os.path.join(root, file)
                    arcname = os.path.relpath(file_path, 'decks')
                    zipf.write(file_path, arcname)
        
        return zip_path