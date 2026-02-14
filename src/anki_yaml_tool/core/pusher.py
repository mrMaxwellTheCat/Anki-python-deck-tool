"""Push YAML-exported decks back to Anki, updating existing notes by ID
or creating new notes when IDs are missing.

Supports three modes:
1. Normal: Add/update notes from YAML, leave existing Anki notes untouched
2. Replace: Sync with YAML - delete notes in Anki not present in YAML
3. Incremental: Only push notes that have changed
"""

import hashlib
import logging
from pathlib import Path
from typing import Any

from anki_yaml_tool.core.config import load_deck_data, load_model_config
from anki_yaml_tool.core.connector import AnkiConnector
from anki_yaml_tool.core.exceptions import AnkiConnectError
from anki_yaml_tool.core.media import get_media_references

# Logger for this module
logger = logging.getLogger("anki_yaml_tool.core.pusher")


def _compute_note_hash(
    note_id: int | None, fields: dict[str, str], tags: list[str]
) -> str:
    """Compute a hash for a note to detect changes."""
    content = f"{note_id}|{','.join(sorted(fields.values()))}|{','.join(sorted(tags))}"
    return hashlib.md5(content.encode("utf-8")).hexdigest()


def _normalize_fields(fields: dict[str, Any]) -> dict[str, str]:
    """Normalize field values to strings."""
    result = {}
    for k, v in fields.items():
        if isinstance(v, dict):
            result[k.lower()] = v.get("value", "")
        else:
            result[k.lower()] = str(v) if v is not None else ""
    return result


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
    replace: bool = False,
    incremental: bool = False,
) -> dict[str, int]:
    """Push notes from an exported deck directory back into Anki.

    Args:
        connector: AnkiConnector instance.
        deck_dir: Directory containing `config.yaml` and `data.yaml` (and optional `media/`).
        deck_name: Optional override for target deck name (otherwise uses config deck-name or provided deck_dir name).
        sync: Whether to trigger AnkiWeb sync after pushing.
        replace: If True, delete notes in Anki that are not present in YAML (sync mode).
        incremental: If True, only push notes that have changed.

    Returns:
        Dictionary with statistics: {"added": X, "updated": Y, "deleted": Z, "unchanged": W, "failed": F}

    Behavior:
        - For each note in `data.yaml`, if `note_id` is present, update fields
          via `updateNoteFields`. Tags are added (not removed).
        - If `note_id` missing, a new note is created using `addNote`.
        - Media files referenced in fields are uploaded if present under `media/`.
        - With replace=True: Delete notes in Anki that don't have matching IDs in YAML
        - With incremental=True: Compare note content and only update if changed
    """
    config_path = deck_dir / "config.yaml"
    data_path = deck_dir / "data.yaml"

    if not config_path.exists() or not data_path.exists():
        raise FileNotFoundError("config.yaml or data.yaml not found in deck directory")

    model_config = load_model_config(config_path)
    items = load_deck_data(data_path)

    target_deck = deck_name or model_config.get("deck-name") or deck_dir.name

    media_dir = deck_dir / "media"

    # Track statistics for summary
    stats = {
        "added": 0,
        "updated": 0,
        "deleted": 0,
        "unchanged": 0,
        "failed": 0,
    }

    # In replace or incremental mode, get existing notes from Anki
    existing_notes: dict[int, dict] = {}
    if replace or incremental:
        try:
            anki_notes = connector.get_notes(str(target_deck))
            for note in anki_notes:
                nid = note.get("noteId") or note.get("note_id") or note.get("id")
                if nid is not None:
                    existing_notes[int(nid)] = note
            logger.info(
                f"Found {len(existing_notes)} existing notes in Anki deck '{target_deck}'"
            )
        except AnkiConnectError as e:
            logger.warning(
                f"Could not fetch existing notes: {e}. Continuing without replace/incremental."
            )
            replace = False
            incremental = False

    # Build a set of YAML note IDs for replace mode
    yaml_note_ids: set[int] = set()
    notes_to_delete_from_yaml: list[int] = []  # Notes marked with _deleted: true

    for item in items:
        nid = item.get("note_id")

        # Check if note is marked as deleted in YAML
        if item.get("_deleted", False) is True:
            if nid is not None:
                try:
                    notes_to_delete_from_yaml.append(int(str(nid)))
                except (ValueError, TypeError):
                    pass
            # Skip processing this item
            continue

        if nid is not None:
            try:
                yaml_note_ids.add(int(str(nid)))
            except (ValueError, TypeError):
                pass

    # Process each note from YAML
    for idx, item in enumerate(items):
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

        # Check if we should skip this note (incremental mode - no changes)
        if incremental and nid is not None:
            try:
                nid_int = int(str(nid))
                existing_note = existing_notes.get(nid_int)
                if existing_note:
                    # Compare fields to detect changes
                    existing_fields = _normalize_fields(existing_note.get("fields", {}))
                    existing_tags = existing_note.get("tags", [])
                    if not isinstance(existing_tags, list):
                        existing_tags = [str(existing_tags)]

                    # Check if content changed
                    yaml_hash = _compute_note_hash(nid_int, mapped_fields, tags)
                    existing_hash = _compute_note_hash(
                        nid_int, existing_fields, existing_tags
                    )

                    if yaml_hash == existing_hash:
                        # No changes, skip this note
                        stats["unchanged"] += 1
                        logger.debug(f"Note {nid_int} unchanged, skipping")
                        continue
            except (ValueError, TypeError):
                pass

        try:
            if nid is not None:
                # Coerce nid to int safely
                nid_int = int(str(nid))
                # Check if note exists in Anki (for replace mode)
                if replace and nid_int not in existing_notes:
                    # Note was deleted in YAML, skip (don't create)
                    logger.debug(
                        f"Note {nid_int} not in existing notes, skipping update"
                    )
                    stats["unchanged"] += 1
                    continue

                # Update existing note
                connector.update_note_fields(nid_int, mapped_fields)
                # Add tags (won't remove existing tags)
                if tags:
                    connector.invoke("addTags", notes=[nid_int], tags=" ".join(tags))
                stats["updated"] += 1
                logger.debug(f"Updated note ID {nid_int}")
            else:
                # Create a new note
                new_nid = connector.add_note(
                    str(target_deck),
                    str(model_config.get("name", "")),
                    mapped_fields,
                    tags,
                )
                stats["added"] += 1
                logger.debug(f"Created new note with ID {new_nid}")
        except AnkiConnectError as e:
            # Check if the error is because the note doesn't exist
            error_msg = str(e).lower()
            note_not_found = (
                "not found" in error_msg
                or "invalid id" in error_msg
                or ("note" in error_msg and "does not exist" in error_msg)
            )

            if nid is not None and note_not_found:
                # Fallback: create a new note since the original note doesn't exist
                logger.warning(
                    f"Note with ID {nid} not found, creating as new note (index {idx + 1}/{len(items)})"
                )
                try:
                    new_nid = connector.add_note(
                        str(target_deck),
                        str(model_config.get("name", "")),
                        mapped_fields,
                        tags,
                    )
                    stats["added"] += 1
                    logger.debug(
                        f"Created new note with ID {new_nid} as fallback for missing note {nid}"
                    )
                except AnkiConnectError:
                    # If creation also fails, log error and continue
                    logger.error(
                        f"Failed to create note (index {idx + 1}/{len(items)}): {e}"
                    )
                    stats["failed"] += 1
            else:
                # For other errors, log and continue
                logger.error(
                    f"Failed to process note (index {idx + 1}/{len(items)}): {e}"
                )
                stats["failed"] += 1

    # Handle replace mode: delete notes in Anki that are not in YAML
    if replace and yaml_note_ids:
        notes_to_delete = [
            nid for nid in existing_notes.keys() if nid not in yaml_note_ids
        ]
        if notes_to_delete:
            logger.info(f"Deleting {len(notes_to_delete)} notes not in YAML...")
            try:
                connector.delete_notes(notes_to_delete)
                stats["deleted"] = len(notes_to_delete)
                logger.info(f"Deleted {len(notes_to_delete)} notes")
            except AnkiConnectError as e:
                logger.error(f"Failed to delete notes: {e}")

    # Handle notes explicitly marked as deleted in YAML (_deleted: true)
    if notes_to_delete_from_yaml:
        logger.info(
            f"Deleting {len(notes_to_delete_from_yaml)} notes marked as deleted in YAML..."
        )
        valid_delete_ids = [
            nid for nid in notes_to_delete_from_yaml if nid in existing_notes
        ]
        if valid_delete_ids:
            try:
                connector.delete_notes(valid_delete_ids)
                stats["deleted"] = stats.get("deleted", 0) + len(valid_delete_ids)
                logger.info(f"Deleted {len(valid_delete_ids)} notes marked in YAML")
            except AnkiConnectError as e:
                logger.error(f"Failed to delete notes from YAML: {e}")

    # Summary
    logger.info(
        f"Push complete: {stats['added']} added, {stats['updated']} updated, "
        f"{stats['deleted']} deleted, {stats['unchanged']} unchanged, {stats['failed']} failed"
    )

    if sync:
        connector.sync()

    return stats
