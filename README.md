# Anki Python Deck Tool

[![Python Version](https://img.shields.io/badge/python-3.10%2B-blue)]()
[![License: GPL-3.0](https://img.shields.io/badge/License-GPL%203.0-blue.svg)](https://opensource.org/licenses/GPL-3.0)
[![CI Status](https://github.com/mrMaxwellTheCat/Anki-python-deck-tool/workflows/CI/badge.svg)](https://github.com/mrMaxwellTheCat/Anki-python-deck-tool/actions)
[![codecov](https://codecov.io/gh/mrMaxwellTheCat/Anki-python-deck-tool/branch/main/graph/badge.svg)](https://codecov.io/gh/mrMaxwellTheCat/Anki-python-deck-tool)

A professional, modular command-line tool to generate Anki decks (`.apkg`) from human-readable YAML source files and push them directly to Anki via AnkiConnect.

## Table of Contents

- [Features](#features)
- [Prerequisites](#prerequisites)
- [Installation](#installation)
- [Quick Start](#quick-start)
- [Usage](#usage)
  - [Building a Deck](#1-build-a-deck-build)
  - [Pushing to Anki](#2-push-to-anki-push)
- [File Formats](#file-formats)
  - [Configuration File (Model)](#configuration-file-model)
  - [Data File (Notes)](#data-file-notes)
- [Project Structure](#project-structure)
- [Development](#development)
- [Future Plans](#future-plans)
- [Contributing](#contributing)
- [License](#license)

## Features

- **YAML-based Workflow**: Define your card models (CSS, templates) and data in clean YAML files.
- **Automated Sync**: Push generated decks directly to a running Anki instance via AnkiConnect.
- **Stable IDs**: Generates deterministic deck and model IDs based on names to preserve study progress across updates.
- **Tag Support**: Automatically handles tags and ID-based tagging for organization.
- **Flexible Architecture**: Modular design supporting multiple note types and custom configurations.
- **Type-Safe**: Modern Python type hints throughout the codebase.
- **Well-Tested**: Comprehensive test suite with pytest.

## Prerequisites

Before using this tool, ensure you have the following:

1.  **Python 3.10+** installed.
2.  **Anki Desktop** installed and running (only required for the `push` command).
3.  **AnkiConnect** add-on installed in Anki (only required for the `push` command).
    *   Open Anki → Tools → Add-ons → Get Add-ons...
    *   Code: `2055492159`
    *   Restart Anki to enable the API (listens on `127.0.0.1:8765`).

## Installation

### Quick Install

It is recommended to install the tool in a virtual environment.

```bash
# Clone the repository
git clone https://github.com/mrMaxwellTheCat/Anki-python-deck-tool.git
cd Anki-python-deck-tool

# Create and activate a virtual environment
python -m venv venv

# On Windows:
.\venv\Scripts\activate

# On Linux/Mac:
source venv/bin/activate

# Install the package
pip install .
```

### Development Installation

For contributing or development work:

```bash
# Install in editable mode with development dependencies
pip install -e ".[dev]"

# Or use the Makefile
make dev

# Set up pre-commit hooks (optional but recommended)
pre-commit install
```

See [CONTRIBUTING.md](CONTRIBUTING.md) for detailed development setup instructions.

## Quick Start

Here's a minimal example to get you started:

1. **Create a configuration file** (`my_model.yaml`):
   ```yaml
   name: "Basic Model"
   fields:
     - "Front"
     - "Back"
   templates:
     - name: "Card 1"
       qfmt: "{{Front}}"
       afmt: "{{FrontSide}}<hr id=answer>{{Back}}"
   css: ".card { font-family: arial; font-size: 20px; text-align: center; }"
   ```

2. **Create a data file** (`my_cards.yaml`):
   ```yaml
   - front: "Hello"
     back: "Bonjour"
     tags: ["basics", "greetings"]

   - front: "Goodbye"
     back: "Au revoir"
     tags: ["basics"]
   ```

3. **Build the deck**:
   ```bash
   anki-yaml-tool build --data my_cards.yaml --config my_model.yaml --output french.apkg --deck-name "French Basics"
   ```

4. **Push to Anki** (optional, requires AnkiConnect):
   ```bash
   anki-yaml-tool push --apkg french.apkg --sync
   ```

## Building Executable

To compile the tool into a single executable file:

```bash
make build-exe
```

The resulting executable will be located in the `dist/` directory.

### Customizing the Icon

To use a custom icon for the executable, place your icon file in the `assets/` directory at the project root.

- **Windows**: `assets/icon.ico`
- **Mac**: `assets/icon.icns`

If these files exist, the build process will automatically use them.

## Usage

The tool provides a CLI entry point `anki-yaml-tool` with two main commands: `build` and `push`.

### 1. Build a Deck (`build`)

Generates an `.apkg` file from your YAML data and configuration.

```bash
anki-yaml-tool-tool-tool build --data data/my_deck.yaml --config configs/japanese_num.yaml --output "My Deck.apkg" --deck-name "Japanese Numbers"
```

**Options:**
- `--data PATH` (Required): Path to the YAML file containing note data.
- `--config PATH` (Required): Path to the YAML file defining the Note Type (Model).
- `--output PATH`: Path where the `.apkg` will be saved (Default: `deck.apkg`).
- `--deck-name TEXT`: Name of the deck inside Anki (Default: `"Generated Deck"`).

**Example with all options:**
```bash
anki-yaml-tool-tool-tool build \\
  --data data/vocabulary.yaml \\
  --config configs/basic_model.yaml \\
  --output builds/vocabulary_v1.apkg \\
  --deck-name "Spanish Vocabulary"
```

### 2. Push to Anki (`push`)

Uploads a generated `.apkg` file to Anki via AnkiConnect.

```bash
anki-yaml-tool-tool-tool push --apkg "My Deck.apkg" --sync
```

**Options:**
- `--apkg PATH` (Required): Path to the `.apkg` file.
- `--sync`: Force a synchronization with AnkiWeb after importing.

**Note**: Ensure Anki is running with the AnkiConnect add-on enabled before using the `push` command.

## File Formats

### Configuration File (Model)

This YAML file defines how your cards look. It specifies the note type structure including fields, card templates, and styling.

**Example: `configs/japanese_num.yaml`**

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

**Configuration Structure:**
- `name` (required): Name of the note type/model in Anki
- `fields` (required): List of field names for the note type
- `templates` (required): List of card templates with `name`, `qfmt` (front), and `afmt` (back)
- `css` (optional): CSS styling for the cards

### Data File (Notes)

This YAML file defines the content of your cards. Field names must match the `fields` in your config (case-insensitive).

**Example: `data/my_deck.yaml`**

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

- numeral: "3"
  kanji: "三"
  reading: "san"
  tags: ["basic", "numbers"]
```

**Data Structure:**
- Each item in the list represents one note/card
- Keys should match field names from the config (case-insensitive)
- `tags` (optional): List of tags to apply to the note
- `id` (optional): Unique identifier that gets added as a special tag (`id::value`)

**Tips:**
- Field values can contain HTML for formatting
- Missing fields will be filled with empty strings
- Tags help organize and filter cards in Anki

## Project Structure

```
Anki-python-deck-tool/
├── .github/
│   ├── workflows/
│   │   ├── ci.yml              # CI pipeline (lint, type-check, test)
│   │   └── release.yml         # Release automation
│   └── copilot-instructions.md # Instructions for GitHub Copilot
├── configs/                     # Example configuration files
│   └── debug_config.yaml
├── data/                        # Example data files
│   └── debug_deck.yaml
├── src/
│   └── anki-yaml-tool/
│       ├── __init__.py
│       ├── cli.py               # CLI entry points
│       └── core/
│           ├── __init__.py
│           ├── builder.py       # Deck building logic
│           ├── connector.py     # AnkiConnect integration
│           └── exceptions.py    # Custom exception classes
├── tests/                       # Test suite
│   ├── __init__.py
│   ├── test_builder.py
│   ├── test_connector.py
│   └── test_exceptions.py
├── .gitignore
├── .pre-commit-config.yaml      # Pre-commit hooks configuration
├── CONTRIBUTING.md              # Development guidelines
├── LICENSE
├── Makefile                     # Common development tasks
├── README.md
├── ROADMAP.md                   # Future development plans
├── pyproject.toml               # Project metadata and tool configs
└── requirements.txt             # Project dependencies
```

## Development

This project welcomes contributions! For detailed setup instructions, coding standards, and workflow guidelines, please see [CONTRIBUTING.md](CONTRIBUTING.md).

### Quick Development Setup

```bash
# Install in development mode
pip install -e ".[dev]"

# Run tests
make test

# Format code
make format

# Lint code
make lint

# Type check
make type-check

# Run all checks
make all
```

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=anki-yaml-tool

# Run specific test file
pytest tests/test_builder.py -v
```

## Future Plans

- **Media Support**: Automatically detect and include media files (images, audio) referenced in YAML.
- **Schema Validation**: Validate YAML structure using pydantic or jsonschema.
- **Multiple Note Types**: Support multiple note types in a single deck build.
- **Verbose Logging**: Add `--verbose` flag for detailed logging.
- **Init Command**: Scaffold new projects with example files (`anki-yaml-tool init`).
- **GUI Interface**: Graphical interface for users who prefer not to use the command line.
- **Packaged Releases**: Standalone executables for Windows, macOS, and Linux.

See [ROADMAP.md](ROADMAP.md) for the complete development roadmap.

## Contributing

We welcome contributions! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for:
- Development environment setup
- Code style guidelines
- Testing requirements
- Pull request process

## License

This project is licensed under the GNU General Public License v3.0 - see the LICENSE file for details.

## Acknowledgments

- Built with [genanki](https://github.com/kerrickstaley/genanki) for Anki package generation
- Uses [AnkiConnect](https://foosoft.net/projects/anki-connect/) for Anki integration
- CLI powered by [Click](https://click.palletsprojects.com/)

---

**Note**: This tool is not affiliated with or endorsed by Anki or AnkiWeb.
