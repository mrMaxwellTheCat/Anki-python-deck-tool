"""Export decks and models from Anki to YAML and media files.

This module provides `export_deck` which fetches notes and model
information via an `AnkiConnector` instance and writes out a directory
containing `config.yaml`, `data.yaml`, and a `media/` folder.
"""

import re
from pathlib import Path

import yaml

from anki_yaml_tool.core.connector import AnkiConnector
from anki_yaml_tool.core.exceptions import AnkiConnectError

IMG_SRC_RE = re.compile(r"<img[^>]+src=[\"']([^\"']+)[\"']")
SOUND_RE = re.compile(r"\[sound:([^\]]+)\]")


# Custom YAML dumper to preserve Unicode and use block style for
# multiline strings (improves readability of LaTeX, HTML, etc.)
class _ReadableDumper(yaml.SafeDumper):
    pass


def _str_representer(dumper, data):
    # Use block style only for multiline strings to preserve single-line
    # values (e.g., LaTeX, Windows paths) and avoid altering round-trip
    # semantics.
    if "\n" in data:
        return dumper.represent_scalar("tag:yaml.org,2002:str", data, style="|")
    return dumper.represent_scalar("tag:yaml.org,2002:str", data)


yaml.add_representer(str, _str_representer, Dumper=_ReadableDumper)


def _extract_media_refs_from_text(text: str) -> set[str]:
    refs = set()
    refs.update(IMG_SRC_RE.findall(text))
    refs.update(SOUND_RE.findall(text))
    return refs


def export_deck(connector: AnkiConnector, deck_name: str, output_dir: Path) -> Path:
    """Export a deck to a directory structure.

    Args:
        connector: AnkiConnector instance
        deck_name: Name of the deck to export
        output_dir: Directory where a subdirectory for the deck will be created

    Returns:
        The path to the created deck directory

    Raises:
        AnkiConnectError: If any AnkiConnect call fails or responses are
            unexpected.
    """
    # 0. Sanitize deck name into a safe directory name and ensure it
    # remains within the intended output directory to prevent path
    # traversal or accidental writes outside the target.
    safe_name = re.sub(r"[^A-Za-z0-9._-]", "_", deck_name)
    deck_path = Path(output_dir) / safe_name
    deck_path.mkdir(parents=True, exist_ok=True)
    try:
        if not str(deck_path.resolve()).startswith(str(Path(output_dir).resolve())):
            raise AnkiConnectError(
                f"Invalid deck name leads to unsafe path: {deck_name}"
            )
    except Exception as e:
        raise AnkiConnectError(f"Failed to create deck output directory: {e}") from e

    # 1. Get notes
    notes = connector.get_notes(deck_name)

    # 2. Determine models used and fetch model definition
    model_names: set[str] = set()
    for note in notes:
        note_model_name = note.get("modelName") or note.get("model_name")
        if note_model_name:
            model_names.add(str(note_model_name))

    if len(model_names) > 1:
        raise AnkiConnectError(
            "Exporting decks with multiple note models is not supported. "
            f"Found models: {', '.join(sorted(model_names))} in deck '{deck_name}'."
        )

    model_name: str | None = None
    if model_names:
        model_name = next(iter(model_names))

    model_config = connector.get_model(model_name) if model_name else None

    # 3. Build config.yaml
    if model_config:
        config_yaml = {
            "name": model_config.get("name", model_name),
            "fields": model_config.get("fields", []),
            "templates": [],
            "css": model_config.get("css", ""),
        }
        # Normalize templates (ensure name, qfmt, afmt)
        for tpl in model_config.get("templates", []):
            cfg_tpl = {
                "name": tpl.get("name") if isinstance(tpl, dict) else str(tpl),
                "qfmt": tpl.get("qfmt", "") if isinstance(tpl, dict) else "",
                "afmt": tpl.get("afmt", "") if isinstance(tpl, dict) else "",
            }
            config_yaml["templates"].append(cfg_tpl)

        with open(deck_path / "config.yaml", "w", encoding="utf-8") as f:
            yaml.dump(
                config_yaml,
                f,
                Dumper=_ReadableDumper,
                default_flow_style=False,
                sort_keys=False,
                allow_unicode=True,
                width=4096,
            )
    else:
        # Minimal fallback config when no model information is available.
        # This ensures a consistent exported structure even for empty decks
        # or when model lookup fails.
        config_yaml = {
            "name": model_name or deck_name,
            "fields": [],
            "templates": [],
            "css": "",
        }
        with open(deck_path / "config.yaml", "w", encoding="utf-8") as f:
            yaml.dump(
                config_yaml,
                f,
                Dumper=_ReadableDumper,
                default_flow_style=False,
                sort_keys=False,
                allow_unicode=True,
                width=4096,
            )

    # 4. Build data.yaml
    data_items = []
    all_media_refs: set[str] = set()

    for note in notes:
        # Note ID
        nid = note.get("noteId") or note.get("note_id") or note.get("id")

        fields = note.get("fields", {})
        # Fields may be mapping to {'Front': {'value': '...'}} or {'Front': '...'}
        normalized: dict[str, str] = {}
        for fname, val in (fields or {}).items():
            if isinstance(val, dict):
                value = val.get("value", "")
            else:
                value = val if isinstance(val, str) else str(val)
            normalized[fname.lower()] = value
            all_media_refs.update(_extract_media_refs_from_text(value))

        item: dict[str, str | list[str]] = {**normalized}
        tags_val = note.get("tags", [])
        item["tags"] = tags_val if isinstance(tags_val, list) else [str(tags_val)]

        if nid is not None:
            item["note_id"] = nid

        data_items.append(item)

    with open(deck_path / "data.yaml", "w", encoding="utf-8") as f:
        yaml.dump(
            data_items,
            f,
            Dumper=_ReadableDumper,
            default_flow_style=False,
            sort_keys=False,
            allow_unicode=True,
            width=4096,
        )

    # 5. Export media files if any
    if all_media_refs:
        media_dir = deck_path / "media"
        media_dir.mkdir(exist_ok=True)
        for ref in all_media_refs:
            try:
                # Validate media reference to prevent path traversal attacks.
                # This validation MUST happen BEFORE retrieving the file to
                # ensure we don't access files outside the media directory.
                ref_path = Path(ref)

                # Reject absolute paths or references containing parent
                # segments (../)
                if ref_path.is_absolute() or ".." in ref_path.parts:
                    continue

                # Build target path and resolve it to detect traversal
                target = media_dir / ref_path
                # Resolve symlinks and relative paths to get the real path
                try:
                    resolved_target = target.resolve()
                    resolved_media_dir = media_dir.resolve()
                except (OSError, RuntimeError):
                    # If path resolution fails, skip this file
                    continue

                # Enforce that the resolved target remains within media_dir
                # This prevents symlink and path traversal attacks
                if not str(resolved_target).startswith(str(resolved_media_dir)):
                    continue

                # Only retrieve the file AFTER validation passes
                content = connector.retrieve_media_file(ref)

                # Ensure parent exists (filenames may include path)
                target.parent.mkdir(parents=True, exist_ok=True)

                with open(target, "wb") as mf:
                    mf.write(content)
            except AnkiConnectError:
                # Log and continue; we don't want a single missing media
                # file to fail the entire export
                continue

    return deck_path
