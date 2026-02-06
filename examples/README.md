# Examples

This directory contains example configurations and data files demonstrating various use cases for the Anki Python Deck Tool.

## Directory Structure

- `basic/` - Simple examples for getting started
- `language-learning/` - Examples for vocabulary and language study
- `math/` - Mathematical formulas and problem-solving
- `technical/` - Examples for programming and technical subjects
- `medical/` - Medical terminology with etymology and definitions
- `historical/` - Historical events with dates and context
- `cloze/` - Cloze deletion style cards for active recall
- `audio/` - Pronunciation practice with IPA and audio support

## Using These Examples

Each example directory contains:
- `config.yaml` - Note type/model configuration
- `data.yaml` - Sample card data
- `README.md` - Specific instructions for that example

To build any example:

```bash
cd examples/<example-name>
anki-yaml-tool build --data data.yaml --config config.yaml --output example.apkg --deck-name "Example Deck"
```

## Contributing Examples

If you have created an interesting deck configuration, we welcome contributions! Please see [CONTRIBUTING.md](../CONTRIBUTING.md) for guidelines.
