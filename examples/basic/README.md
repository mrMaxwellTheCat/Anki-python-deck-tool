# Basic Example

This is the simplest possible Anki deck configuration - a basic front/back flashcard.

## Files

- `config.yaml` - Defines a "Basic Flashcard" note type with two fields (Front and Back)
- `data.yaml` - Sample questions covering various topics

## Building

```bash
anki-yaml-tool build --data data.yaml --config config.yaml --output basic.apkg --deck-name "Basic Flashcards"
```

## Customization

You can easily customize this template:

1. **Change styling**: Edit the `css` section in `config.yaml`
2. **Add more cards**: Add more entries to `data.yaml`
3. **Add tags**: Use the `tags` field to organize your cards
4. **Add IDs**: Use the `id` field to create permanent identifiers

## Example with ID

```yaml
- front: "My custom question"
  back: "My custom answer"
  tags: ["custom"]
  id: "custom_001"
```

The ID will be added as a special tag (`id::custom_001`) in Anki.
