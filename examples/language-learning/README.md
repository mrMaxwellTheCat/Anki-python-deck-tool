# Language Learning Example

This example demonstrates a vocabulary card template suitable for language learning, with multiple fields and bidirectional cards.

## Features

- **Four fields**: Word, Translation, Example sentence, and Pronunciation
- **Two card types**: 
  - Recognition (see word → recall translation)
  - Recall (see translation → produce word)
- **Conditional display**: Pronunciation and examples only shown if provided
- **Professional styling**: Clean, readable design optimized for mobile and desktop

## Files

- `config.yaml` - "Vocabulary Card" note type with bidirectional templates
- `data.yaml` - Sample French vocabulary with basic phrases

## Building

```bash
anki-tool build --data data.yaml --config config.yaml --output french_vocab.apkg --deck-name "French Basics"
```

## Customization Ideas

### 1. Add Audio Files

You can add audio pronunciation by including audio files:

```yaml
- word: "Bonjour"
  translation: "Hello"
  pronunciation: "[sound:bonjour.mp3]"
  example: "Bonjour, comment allez-vous?"
```

### 2. Add Images

Include images for visual learning:

```yaml
- word: "Chat"
  translation: "Cat"
  example: "J'ai un chat noir."
  image: "<img src='cat.jpg'>"
```

### 3. Additional Fields

Extend the note type with more fields:
- Gender (for nouns)
- Part of speech
- Conjugation table
- Related words
- Mnemonics

### 4. Different Languages

This template works for any language pair:
- Spanish ↔ English
- Japanese ↔ English
- German ↔ English
- Or any other combination

Just update the data file with your target language vocabulary.

## Tags

The example uses tags for organization:
- Language identifier (e.g., "french", "spanish")
- Topic/category (e.g., "greetings", "food")
- Level (e.g., "a1", "b2" for CEFR levels)

Use tags to create focused study sessions in Anki!
