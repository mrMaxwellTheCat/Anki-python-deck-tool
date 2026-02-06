# Historical Events Example

This example demonstrates a deck for learning important historical dates and events with context and significance.

## Files

- `config.yaml` - "Historical Events" note type with bidirectional templates
- `data.yaml` - Sample historical events from various eras

## Features

- **Bidirectional cards**: Learn both date-to-event and event-to-date
- **Historical context**: Understanding why events occurred
- **Significance**: Long-term impact and importance
- **Era classification**: Organize by historical period
- **Rich styling**: Period-appropriate design with serif fonts

## Usage

Build the deck:

```bash
anki-yaml-tool build \
  --data examples/historical/data.yaml \
  --config examples/historical/config.yaml \
  --output historical_events.apkg \
  --deck-name "Historical Events"
```

## Customization

### Adding more events

Extend the data file with events from:
- Ancient history (Roman Empire, Ancient Greece, etc.)
- Medieval period
- Renaissance
- Modern conflicts
- Scientific discoveries
- Cultural movements

### Field suggestions

Consider adding:
- `location` - Where the event occurred
- `key_figures` - Important people involved
- `related_events` - Connected historical events
- `image` - Historical photographs or artwork
- `sources` - References for further reading

## Tags

The example uses tags to organize events by:
- Time period (18th-century, 19th-century, etc.)
- Region (american-history, european-history, etc.)
- Type (revolution, war, exploration, etc.)

## Tips for Learning

- Start with major events and expand to details
- Create connections between related events
- Add geographical context with maps
- Include primary source quotes for important documents
