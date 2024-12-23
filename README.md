# Deck Manager

## Overview
The Deck Manager application is a Python-based tool designed to manage, search, and download card decks. It uses the [Scryfall API](https://scryfall.com/docs/api) to retrieve detailed card data and images, automates deck management, and provides a user-friendly interface via a Flask web application.

## Features
- **Deck Management**: Create, organize, and store decks with card details and images.
- **Scryfall Integration**: Fetch card data, including high-resolution images, using the Scryfall API.
- **Zip Decks**: Export decks as downloadable ZIP files.
- **Web Interface**: Interact with the application through a Flask-powered web interface.
- **Cleanup Utilities**: Remove old decks or unused files via the web interface.

## Requirements
- Python 3.8+
- Required Python libraries:
  - Flask
  - Requests
- Internet connection for API calls to Scryfall.

## Code Structure
- deck.py: Core logic for deck and card management.
    - Deck: Handles deck operations like populating card lists, retrieving data, and downloading images.
    - Card: Represents individual card data.
    - DeckBox: Processes user input to create Deck objects.
- app.py: Flask web server.
    - Routes:
    - /: Homepage.
    - /search_decklist: Process deck creation requests.
    - /ready_decks: View and download prepared decks.
    - /download_deck/<filename>: Download specific decks.
    - /clean_folder: Clean up the decks folder.
    - /help: Help page.
- Templates:
    - index.html: Homepage for creating decks.
    - ready_decks.html: Lists available decks for download.
    - help.html: Provides guidance on using the application.

## Example Deck Data Format
    
    4 Lightning Bolt
    2 Counterspell 2ED 100
    1 Black Lotus LEA 233
  
- Explanation:
    - Quantity: Number of copies of the card.
    - Card Name: Full name of the card.
    - Set Code (Optional): 3-letter set code.
    - Collector Number (Optional): Specific collector number.

## Example

You can test it on https://grimoire-nuya.onrender.com/

## Contact
For any inquiries or issues, please contact [luis.filipe@edu.pucrs.br](mailto:luis.filipe@edu.pucrs.br).
