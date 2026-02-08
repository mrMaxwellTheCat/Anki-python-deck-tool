"""Push YAML-exported decks back to Anki, updating existing notes by ID
or creating new notes when IDs are missing.
"""

from pathlib import Path

from anki_yaml_tool.core.config import load_deck_data, load_model_config
from anki_yaml_tool.core.connector import AnkiConnector
from anki_yaml_tool.core.exceptions import AnkiConnectError
from anki_yaml_tool.core.media import get_media_references


def _map_fields_for_model(model_fields: list[str], data_item: dict) -> dict[str, str]:
    """Return a mapping of model field names to values based on the data item.

    The data item uses lowercase keys (exporter normalizes to lowercase), so
    we look up each model field by its lowercase name.
    """
    mapped: dict[str, str] = {}
    for field_name in model_fields:
        key = field_name.lower()
        val = data_item.get(key, "")
        mapped[field_name] = str(val)
    return mapped


def push_deck_from_dir(
    connector: AnkiConnector,
    deck_dir: Path,
    deck_name: str | None = None,
    sync: bool = False,
) -> None:
    """Push notes from an exported deck directory back into Anki.

    Args:
        connector: AnkiConnector instance.
        deck_dir: Directory containing `config.yaml` and `data.yaml` (and optional `media/`).
        deck_name: Optional override for target deck name (otherwise uses config deck-name or provided deck_dir name).
        sync: Whether to trigger AnkiWeb sync after pushing.

    Behavior:
        - For each note in `data.yaml`, if `note_id` is present, update fields
          via `updateNoteFields`. Tags are added (not removed).
        - If `note_id` missing, a new note is created using `addNote`.
        - Media files referenced in fields are uploaded if present under `media/`.
    """
    config_path = deck_dir / "config.yaml"
    data_path = deck_dir / "data.yaml"

    if not config_path.exists() or not data_path.exists():
        raise FileNotFoundError("config.yaml or data.yaml not found in deck directory")

    model_config = load_model_config(config_path)
    items = load_deck_data(data_path)

    target_deck = deck_name or model_config.get("deck-name") or deck_dir.name

    media_dir = deck_dir / "media"

    for item in items:
        # Prepare fields mapping
        mapped_fields = _map_fields_for_model(model_config["fields"], item)

        # Upload referenced media if available
        text_values = " ".join(mapped_fields.values())
        refs = get_media_references(text_values)
        for ref in refs:
            media_file = media_dir / ref
            if media_file.exists():
                connector.store_media_file(media_file, filename=ref)

        # Tags
        tags = item.get("tags", [])
        if not isinstance(tags, list):
            tags = [str(tags)]

        nid = item.get("note_id")
        try:
            if nid is not None:
                # Coerce nid to int safely
                nid_int = int(str(nid))
                # Update existing note
                connector.update_note_fields(nid_int, mapped_fields)
                # Add tags (won't remove existing tags)
                if tags:
                    connector.invoke("addTags", notes=[nid_int], tags=" ".join(tags))
            else:
                # Create a new note
                connector.add_note(
                    target_deck, model_config["name"], mapped_fields, tags
                )
        except AnkiConnectError:
            # Surface the error but continue with other notes
            raise

    if sync:
        connector.sync()
