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
from typing import Any, cast

from anki_yaml_tool.core.builder import ModelConfigComplete
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

    # Create a case-insensitive lookup map for data items
    data_lookup = {k.lower(): v for k, v in data_item.items()}

    for field_name in model_fields:
        key = field_name.lower()
        val = data_lookup.get(key, "")
        mapped[field_name] = str(val)
    return mapped


def _push_deck_data(
    connector: AnkiConnector,
    model_config: ModelConfigComplete,
    items: list[dict[str, str | list[str]]],
    media_dir: Path | None,
    deck_name_override: str | None = None,
    sync: bool = False,
    replace: bool = False,
    incremental: bool = False,
) -> dict[str, int]:
    """Internal function to push loaded deck data to Anki."""
    target_deck = deck_name_override or model_config.get("deck-name")
    if not target_deck:
        # Should be caught by caller, but safe fallback
        target_deck = "Default"

    # Ensure deck exists
    try:
        connector.invoke("createDeck", deck=target_deck)
    except AnkiConnectError as e:
        logger.warning(f"Failed to ensure deck exists: {e}")

    # Track statistics for summary
    stats = {
        "added": 0,
        "updated": 0,
        "deleted": 0,
        "unchanged": 0,
        "failed": 0,
    }

    # Ensure model exists
    model_name = model_config.get("name")
    if model_name:
        try:
            existing_models = connector.get_model_names()
            if model_name not in existing_models:
                logger.info(f"Model '{model_name}' not found. Creating it...")
                # Prepare card templates
                raw_templates = model_config.get("templates")
                final_templates = []
                if raw_templates:
                    for t in raw_templates:
                        # Handle both dict and Pydantic model dump
                        t_dict = t if isinstance(t, dict) else t.model_dump()
                        name = t_dict.get("name", "Card 1")
                        front = t_dict.get("qfmt") or t_dict.get("Front") or ""
                        back = t_dict.get("afmt") or t_dict.get("Back") or ""
                        final_templates.append(
                            {"Name": name, "Front": front, "Back": back}
                        )
                else:
                    # Generate default template using actual field names
                    fields = model_config.get("fields", ["Front", "Back"])
                    f1 = fields[0] if len(fields) > 0 else "Front"
                    f2 = fields[1] if len(fields) > 1 else f1
                    final_templates.append(
                        {
                            "Name": "Card 1",
                            "Front": f"{{{{{f1}}}}}",
                            "Back": f"{{{{FrontSide}}}}<hr id=answer>{{{{{f2}}}}}",
                        }
                    )

                connector.create_model(
                    model_name=model_name,
                    in_order_fields=model_config.get("fields", ["Front", "Back"]),
                    css=model_config.get("css", ""),
                    is_cloze=model_config.get("isCloze", False),
                    card_templates=final_templates,
                )
                logger.info(f"Created model '{model_name}'")
        except AnkiConnectError as e:
            logger.error(f"Failed to check/create model: {e}")
            # We continue, maybe it exists but get_model_names failed?
            # Or add_note will fail later, which is handled.

    # Check for template mismatch in existing model
    if model_name:
        try:
            model_def = connector.get_model(model_name)
            existing_templates = model_def.get("templates", [])

            # Prepare intended templates
            raw_templates = model_config.get("templates")
            final_templates = []
            if raw_templates:
                for t in raw_templates:
                    t_dict = t if isinstance(t, dict) else t.model_dump()
                    final_templates.append(
                        {
                            "Name": t_dict.get("name", "Card 1"),
                            "Front": t_dict.get("qfmt") or t_dict.get("Front") or "",
                            "Back": t_dict.get("afmt") or t_dict.get("Back") or "",
                        }
                    )
            else:
                # Generate default template using actual field names
                fields = model_config.get("fields", ["Front", "Back"])
                f1 = fields[0] if len(fields) > 0 else "Front"
                f2 = fields[1] if len(fields) > 1 else f1
                final_templates.append(
                    {
                        "Name": "Card 1",
                        "Front": f"{{{{{f1}}}}}",
                        "Back": f"{{{{FrontSide}}}}<hr id=answer>{{{{{f2}}}}}",
                    }
                )

            existing_fields = model_def.get("fields", [])
            existing_first_field = existing_fields[0] if existing_fields else "Front"
            updates = {}
            # Update matching templates and suppress extras
            yaml_tmpl_names = {t["Name"] for t in final_templates}

            for ext_tmpl in existing_templates:
                name = ext_tmpl["Name"]
                if name in yaml_tmpl_names:
                    # Update content to match YAML
                    target = next(t for t in final_templates if t["Name"] == name)
                    target_front = target["Front"]
                    target_back = target["Back"]

                    if (
                        ext_tmpl.get("Front") != target_front
                        or ext_tmpl.get("Back") != target_back
                    ):
                        updates[name] = {
                            "Front": target_front,
                            "Back": target_back,
                            "qfmt": target_front,
                            "afmt": target_back,
                        }
                else:
                    # Extra template in Anki! Suppress it.
                    # Use {{#FirstField}}{{/FirstField}} pattern which renders empty but is valid for Anki
                    logger.warning(
                        f"Suppressing extra template '{name}' in model '{model_name}'"
                    )
                    # Use simple string concatenation to avoid f-string brace escaping hell
                    suppress_val = (
                        "{{#"
                        + existing_first_field
                        + "}}{{/"
                        + existing_first_field
                        + "}}"
                    )
                    updates[name] = {
                        "Front": suppress_val,
                        "Back": "",
                        "qfmt": suppress_val,
                        "afmt": "",
                    }

            if updates:
                logger.info(
                    f"Updating {len(updates)} templates in model '{model_name}'"
                )
                connector.update_model_templates(model_name, updates)

        except Exception as e:
            logger.warning(f"Failed to sync model templates: {e}")

    # In replace or incremental mode, OR if we need to look up IDs (any item missing ID),
    # get existing notes from Anki

    # Check if we need to lookup IDs
    needs_id_lookup = any(item.get("note_id") is None for item in items)

    existing_notes: dict[int, dict] = {}
    if replace or incremental or needs_id_lookup:
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
                f"Could not fetch existing notes: {e}. duplicate handling might fail."
            )
            # If we needed lookup but failed, we might create duplicates.
            # But we proceed. replace/incremental are disabled on error.
            replace = False
            incremental = False

    # Build a set of YAML note IDs for replace mode
    yaml_note_ids: set[int] = set()
    notes_to_delete_from_yaml: list[int] = []  # Notes marked with _deleted: true

    # Build a lookup map for existing notes by their first field value
    # This allows matching YAML notes to Anki notes when note_id is missing
    # (e.g., when creating a deck from scratch or manual YAML editing)
    existing_notes_by_first_field: dict[str, int] = {}
    if existing_notes:
        for nid, note in existing_notes.items():
            fields = note.get("fields", {})
            # Get the first field value (Anki's sort field / primary key equivalent)
            if fields:
                # Anki returns fields as {"Front": {"value": "...", "order": 0}, ...}
                # We need to find the field with order 0, or just use the first one if not sorted
                # Actually, AnkiConnect returns fields as a dict. Order might not be preserved.
                # But typically "Front" or the first defined field is key.
                # Let's try to be smart: use the model's first field name if available
                first_field_name = (
                    model_config["fields"][0] if model_config.get("fields") else None
                )
                first_val = ""

                if first_field_name:
                    # Case-insensitive lookup for field name
                    for f_name, f_data in fields.items():
                        if f_name.lower() == first_field_name.lower():
                            if isinstance(f_data, dict):
                                first_val = f_data.get("value", "")
                            else:
                                first_val = str(f_data)
                            break

                if first_val:
                    existing_notes_by_first_field[first_val] = nid

    for item in items:
        # Cast to dict to satisfy type checker (items is list[dict[str, str|list[str]]])
        item_dict = cast(dict[str, Any], item)
        nid = item_dict.get("note_id")

        # If ID is missing, try to lookup by first field
        if nid is None:
            # Map fields from YAML to get the first field value
            mapped = _map_fields_for_model(model_config["fields"], item_dict)
            if model_config.get("fields"):
                first_field = model_config["fields"][0]
                first_val = mapped.get(first_field, "")

                if first_val in existing_notes_by_first_field:
                    nid = existing_notes_by_first_field[first_val]
                    # Update the item with the found ID so we treat it as an update later
                    item_dict["note_id"] = nid
                    logger.debug(
                        f"Matched YAML note '{first_val[:20]}...' to existing ID {nid}"
                    )

        # Check if note is marked as deleted in YAML
        if item_dict.get("_deleted", False) is True:
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
        item_dict = cast(dict[str, Any], item)

        # Prepare fields mapping
        mapped_fields = _map_fields_for_model(model_config["fields"], item_dict)

        # Upload referenced media if available
        if media_dir:
            text_values = " ".join(mapped_fields.values())
            refs = get_media_references(text_values)
            for ref in refs:
                media_file = media_dir / ref
                if media_file.exists():
                    connector.store_media_file(media_file, filename=ref)

        # Tags
        tags = item_dict.get("tags", [])
        if not isinstance(tags, list):
            tags = [str(tags)]

        nid = item_dict.get("note_id")

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


def push_deck_from_dir(
    connector: AnkiConnector,
    deck_dir: Path,
    deck_name: str | None = None,
    sync: bool = False,
    replace: bool = False,
    incremental: bool = False,
) -> dict[str, int]:
    """Push notes from an exported deck directory back into Anki."""
    config_path = deck_dir / "config.yaml"
    data_path = deck_dir / "data.yaml"

    if not config_path.exists() or not data_path.exists():
        raise FileNotFoundError("config.yaml or data.yaml not found in deck directory")

    model_config = load_model_config(config_path)
    items = load_deck_data(data_path)
    # The config.py load_deck_data returns list[dict[str, str | list[str]]]
    # but uses TypeVar or internal logic. We cast it or trust it.

    # Use directory name as fallback for deck name
    final_deck_name = deck_name or model_config.get("deck-name") or deck_dir.name
    media_dir = deck_dir / "media"

    return _push_deck_data(
        connector=connector,
        model_config=model_config,
        items=items,
        media_dir=media_dir,
        deck_name_override=final_deck_name,
        sync=sync,
        replace=replace,
        incremental=incremental,
    )


def push_deck_from_file(
    connector: AnkiConnector,
    deck_path: Path,
    deck_name: str | None = None,
    sync: bool = False,
    replace: bool = False,
    incremental: bool = False,
) -> dict[str, int]:
    """Push notes from a single deck file back into Anki."""
    from anki_yaml_tool.core.config import load_deck_file

    if not deck_path.exists():
        raise FileNotFoundError(f"Deck file not found: {deck_path}")

    model_config, items, file_deck_name, media_folder = load_deck_file(deck_path)

    # Use file base name or file-defined deck name if no override provided
    final_deck_name = deck_name or file_deck_name or deck_path.stem

    return _push_deck_data(
        connector=connector,
        model_config=model_config,
        items=items,
        media_dir=media_folder,
        deck_name_override=final_deck_name,
        sync=sync,
        replace=replace,
        incremental=incremental,
    )
