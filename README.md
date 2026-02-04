# Anki Python Deck Tool

A professional, modular tool to generate Anki decks from YAML source files and push them automatically to Anki.

## Structure

- `configs/`: Contains YAML files defining the Anki Model (fields, templates, CSS).
- `data/`: Contains your deck data (YAML) and media files.
- `src/anki_tool/`:
    - `core/builder.py`: Logic for creating `.apkg` files using `genanki`.
    - `core/connector.py`: Logic for communicating with AnkiConnect.
    - `cli.py`: Command-line interface.

## Quick Start

### 1. Build a Deck
Generate an `.apkg` file from your data and configuration:
```bash
python src/anki_tool/cli.py build --data data/my_deck.yaml --config configs/japanese_num.yaml --output data/my_deck.apkg --deck-name "My Deck"
```

### 2. Push to Anki
Import the generated package into a running Anki instance (requires AnkiConnect):
```bash
python src/anki_tool/cli.py push --apkg data/my_deck.apkg
```

## Future Plans
- **Media Support**: Automatically detect and include media files referenced in YAML.
- **GUI**: A graphical interface for users who prefer not to use the command line.
- **Validation**: Schema validation for data and config files.
