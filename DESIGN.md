# Desired Behavior
## Basic Functionality
Commands:
- `new [yaml file]`: Creates **new** anki deck based on the provided YAML file.
- `update [yaml file]`: Updates an existing anki deck based on the provided YAML file. If the deck does not exist, give an error message. Changes, additions, and deletions in card/notes should be reflected in the anki deck.
- `pull [yaml file]`: Pulls the current state of the anki deck into the provided YAML file. If the deck does not exist, give an error message. Would overwrite YAMl if already exists.

## YAML File Structure


```yaml
deck-name: 'Example deck' # Name of the deck
config:
  fields: # Fields each note will have
    - field-1
    - field-2
    - field-3
  css: # CSS here; recommended | for multi-line
  templates: # Templates for the cards; each template will be a card type in anki
    - name: Card type 1 # Name of the card type
      qfmt: | # Question format
        {{field-1}}
      afmt: | # Answer format
        {{FrontSide}}
        <hr id=answer>
        <div class="destino">{{field-2}}</div>
  media-folder: "path/to/media/folder" # Optional; if specified, media files in this folder will be added to the anki deck
data:
  - field-1: 'field-1 value for note 1'
    field-2: 'field-2 value for note 1'
    field-3: 'field-3 value for note 1'
  - field-1: 'field-1 value for note 2'
    field-2: 'field-2 value for note 2'
    field-3: 'field-3 value for note 2'
```

## Additional Features
- GUI: complete GUI for using every feature of the tool
- `watch [yaml file]`: Watches the provided YAML file for changes and automatically updates the anki deck when changes are detected.
- Media: Support for adding media using field for file path or URL; media files in the specified media folder will be added to the anki deck.
- pulling config from another yaml file
