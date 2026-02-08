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
    # Use block style for multiline strings
    if "\n" in data or "\\" in data:
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
    deck_dir_name = deck_name.replace("::", "_").replace(" ", "_")
    deck_path = Path(output_dir) / deck_dir_name
    deck_path.mkdir(parents=True, exist_ok=True)

    # 1. Get notes
    notes = connector.get_notes(deck_name)

    # 2. Determine models used and fetch model definition for the first model
    model_name = None
    if notes:
        model_name = notes[0].get("modelName") or notes[0].get("model_name")

    model_config = None
    if model_name:
        model_config = connector.get_model(model_name)

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
                content = connector.retrieve_media_file(ref)
                target = media_dir / ref
                # Ensure parent exists (filenames may include path)
                target.parent.mkdir(parents=True, exist_ok=True)
                with open(target, "wb") as mf:
                    mf.write(content)
            except AnkiConnectError:
                # Log and continue; we don't want a single missing media
                # file to fail the entire export
                continue

    return deck_path
