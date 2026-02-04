# Anki Python Deck Tool

[![Python Version](https://img.shields.io/badge/python-3.8%2B-blue)]()

A professional, modular command-line tool to generate Anki decks (`.apkg`) from human-readable YAML source files and push them directly to Anki via AnkiConnect.

## Features

- **YAML-based Workflow**: Define your card models (CSS, templates) and data in clean YAML files.
- **Automated Sync**: Push generated decks directly to a running Anki instance.
- **Stable IDs**: Generates deck IDs based on names to preserve study progress across updates.
- **Tag Support**: Automatically handles tags and ID-based tagging.

## Prerequisites

Before using this tool, ensure you have the following:

1.  **Python 3.8+** installed.
2.  **Anki Desktop** installed and running.
3.  **AnkiConnect** add-on installed in Anki.
    *   Open Anki -> Tools -> Add-ons -> Get Add-ons...
    *   Code: `2055492159`
    *   Restart Anki to enable the API (listens on `127.0.0.1:8765`).

## Installation

It is recommended to install the tool in a virtual environment.

```bash
# Clone the repository
git clone https://github.com/yourusername/anki-tool.git
cd anki-tool

# Create a virtual environment
python -m venv venv
# Windows:
.\venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate

# Install dependencies
pip install .

# For development (editable mode)
pip install -e .
```

## Usage

The tool provides a CLI entry point `anki-tool` with two main commands: `build` and `push`.

### 1. Build a Deck (`build`)
Generates an `.apkg` file from your YAML data and configuration.

```bash
anki-tool build --data data/my_deck.yaml --config configs/japanese_num.yaml --output "My Deck.apkg" --deck-name "Japanese Numbers"
```

**Options:**
- `--data PATH` (Required): Path to the YAML file containing note data.
- `--config PATH` (Required): Path to the YAML file defining the Note Type (Model).
- `--output PATH`: Path where the `.apkg` will be saved (Default: `deck.apkg`).
- `--deck-name TEXT`: Name of the deck inside Anki (Default: `"Generated Deck"`).

### 2. Push to Anki (`push`)
Uploads a generated `.apkg` file to Anki.

```bash
anki-tool push --apkg "My Deck.apkg" --sync
```

**Options:**
- `--apkg PATH` (Required): Path to the `.apkg` file.
- `--sync`: Force a synchronization with AnkiWeb after importing.

## File Formats

### Configuration File (Model)
This dictionary defines how your cards look.
Example: `configs/japanese_num.yaml`

```yaml
name: "Japanese Numbers Model"  # Name of the Note Type in Anki
css: |
  .card {
   font-family: arial;
   font-size: 20px;
   text-align: center;
   color: black;
   background-color: white;
  }
  .highlight { color: red; }

fields:
  - "Numeral"
  - "Kanji"
  - "Reading"

templates:
  - name: "Card 1: Numeral -> Kanji"
    qfmt: "{{Numeral}}"         # Front side HTML
    afmt: |                     # Back side HTML
      {{FrontSide}}
      <hr id=answer>
      {{Kanji}}<br>
      <span class="highlight">{{Reading}}</span>
```

### Data File (Notes)
This list defines the content of your cards. Key names must match the `fields` in your config (case-insensitive).
Example: `data/my_deck.yaml`

```yaml
- numeral: "1"
  kanji: "一"
  reading: "ichi"
  tags:
    - "basic"
    - "numbers"
  id: "num_001" # Optional: Adds an 'id::num_001' tag

- numeral: "2"
  kanji: "二"
  reading: "ni"
  tags: ["basic"]
```

## Project Structure

```
├── configs/            # Configs for Note Types (Models)
├── data/               # Deck content files
├── src/
│   └── anki_tool/
│       ├── cli.py      # Entry point
│       └── core/       # Application logic
└── pyproject.toml      # Project metadata
```

## Future Plans
- **Media Support**: Automatically detect and include media files referenced in YAML.
- **GUI**: A graphical interface for users who prefer not to use the command line.
- **Validation**: Schema validation for data and config files.
