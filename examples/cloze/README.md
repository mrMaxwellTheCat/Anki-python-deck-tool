# Cloze Deletion Example

This example demonstrates a deck using cloze deletion style, where specific parts of text are hidden for active recall.

## Files

- `config.yaml` - "Cloze Deletion" note type with highlighted answers
- `data.yaml` - Sample cloze cards across various subjects

## Features

- **Visual cloze markers**: Uses `<span class='cloze'>` to highlight answers
- **Context retention**: Full sentence preserved for better understanding
- **Hints**: Optional hints to guide recall
- **Extra information**: Additional context revealed after answer
- **Category organization**: Group by subject area
- **Clean styling**: Readable layout with highlighted cloze deletions

## Usage

Build the deck:

```bash
anki-yaml-tool build \
  --data examples/cloze/data.yaml \
  --config examples/cloze/config.yaml \
  --output cloze_deletion.apkg \
  --deck-name "Cloze Deletion Cards"
```

## About Cloze Deletion

Cloze deletion is an effective study technique where:
- You see a sentence with one or more parts hidden
- You must recall the hidden information
- The context helps trigger memory

This format is excellent for:
- Factual information
- Definitions
- Formulas
- Historical dates
- Terminology

## Note on Implementation

This example uses a simplified cloze format with visual highlighting. Anki's native cloze note type offers additional features like:
- Multiple overlapping clozes from the same text
- Automatic card generation for each cloze
- Special `{{c1::text}}` syntax

For native Anki cloze functionality, you would need to import cards differently. This example demonstrates how to create cloze-style cards using the standard note type approach.

## Customization

### Creating effective cloze cards

1. **One concept per card**: Focus on a single piece of information
2. **Provide context**: Include enough surrounding information
3. **Use hints wisely**: Give clues without revealing the answer
4. **Add extra info**: Deepen understanding with additional context
5. **Group by topic**: Use tags and categories to organize

### Field suggestions

Consider adding:
- `source` - Reference material
- `image` - Visual aids
- `mnemonic` - Memory triggers
- `difficulty` - Self-rated difficulty level

## Tags

The example uses tags to organize cards by:
- Subject (biology, mathematics, history, etc.)
- Topic (cell-biology, algebra, shakespeare, etc.)
- Type (formulas, dates, definitions, etc.)
