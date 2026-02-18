"""Core deck service functions.

This module contains the pure business logic for building, validating,
and pushing Anki decks.  CLI commands delegate to these functions so that
the same logic can be reused by the future GUI or any other frontend.
"""

from __future__ import annotations

import base64
import json
import logging
import re
import zipfile
from dataclasses import dataclass, field
from pathlib import Path
from typing import cast

from anki_yaml_tool.core.adapter import AnkiAdapter
from anki_yaml_tool.core.builder import AnkiBuilder, ModelConfigComplete
from anki_yaml_tool.core.config import load_deck_file
from anki_yaml_tool.core.exceptions import MediaMissingError
from anki_yaml_tool.core.media import (
    discover_media_files,
    get_media_references,
    validate_media_file,
)
from anki_yaml_tool.core.validators import (
    check_duplicate_ids,
    validate_html_tags,
    validate_note_fields,
)

logger = logging.getLogger("anki_yaml_tool.core.deck_service")


# ---------------------------------------------------------------------------
# Data classes for service results
# ---------------------------------------------------------------------------


@dataclass
class ValidationIssue:
    """A single validation warning or error.

    Attributes:
        level: Either ``"error"`` or ``"warning"``.
        message: Human-readable description of the issue.
    """

    level: str  # "error" | "warning"
    message: str


@dataclass
class ValidationResult:
    """Outcome of :func:`validate_deck`.

    Attributes:
        issues: All warnings and errors found during validation.
        has_errors: ``True`` if at least one error-level issue was found.
        has_warnings: ``True`` if at least one warning-level issue was found.
    """

    issues: list[ValidationIssue] = field(default_factory=list)

    @property
    def has_errors(self) -> bool:
        """Return True if any error-level issues exist."""
        return any(i.level == "error" for i in self.issues)

    @property
    def has_warnings(self) -> bool:
        """Return True if any warning-level issues exist."""
        return any(i.level == "warning" for i in self.issues)


@dataclass
class BuildResult:
    """Outcome of :func:`build_deck`.

    Attributes:
        output_path: Path to the generated ``.apkg`` file.
        deck_name: Resolved name of the deck.
        notes_processed: Number of notes written.
        media_files: Number of media files added.
        missing_media_refs: Filenames of referenced but missing media.
    """

    output_path: Path
    deck_name: str
    notes_processed: int = 0
    media_files: int = 0
    missing_media_refs: list[str] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Public service functions
# ---------------------------------------------------------------------------


def _resolve_deck_name(
    deck_name_override: str | None,
    file_deck_name: str | None,
    deck_path: Path,
) -> str:
    """Determine the final deck name from overrides and fallbacks.

    Args:
        deck_name_override: CLI-supplied override (highest priority).
        file_deck_name: Deck name read from the YAML file.
        deck_path: Path to the deck file (used as last-resort fallback).

    Returns:
        The resolved deck name.
    """
    if deck_name_override is not None:
        return deck_name_override

    if file_deck_name is not None:
        return file_deck_name

    # Fallback: use parent directory name for `deck.yaml`, else stem
    if deck_path.stem == "deck":
        return deck_path.parent.name or "Deck"
    return deck_path.stem


# Special Anki template variables that should be ignored in field checks
ANKI_SPECIAL_VARS = {
    "frontside",  # Contains the question (front) side
    "front",  # Front field
    "back",  # Back field
    "type",  # Type (cloze)
    "card",  # Card number
    "tags",  # Tags
}


def _extract_template_fields(template: dict) -> set[str]:
    """Extract field names used in a template's qfmt and afmt.

    Args:
        template: Template dictionary with 'qfmt' and/or 'afmt' keys.

    Returns:
        Set of field names (without {{ }}) used in the template,
        excluding Anki special variables.
    """
    fields: set[str] = set()
    # Pattern to match {{FieldName}} or {{FieldName|filter}}
    pattern = r"\{\{\s*([^}|]+)(?:\|[^}]+)?\s*\}\}"

    for fmt_key in ("qfmt", "afmt"):
        if fmt_key in template:
            content = template[fmt_key]
            matches = re.findall(pattern, content)
            for match in matches:
                # Skip Anki special variables (case-insensitive)
                if match.lower() not in ANKI_SPECIAL_VARS:
                    fields.add(match)

    return fields


def _get_empty_fields_for_templates(
    item: dict,
    model_config: ModelConfigComplete,
    fields: list[str],
) -> dict[str, set[str]]:
    """Check which template fields are empty for a given item.

    Args:
        item: Note data dictionary.
        model_config: Model configuration with templates.
        fields: List of field names in the model.

    Returns:
        Dictionary mapping template name to set of empty field names.
    """
    item_lower = {k.lower(): v for k, v in item.items()}
    empty_by_template: dict[str, set[str]] = {}

    templates = model_config.get("templates", [])
    for tpl in templates:
        tpl_name = tpl.get("name", "Unnamed")
        tpl_fields = _extract_template_fields(tpl)

        # Check which fields are empty (None, empty string, or not present)
        empty_fields: set[str] = set()
        for field in tpl_fields:
            value = item_lower.get(field.lower(), "")
            # Convert to string and check if empty
            if not str(value).strip():
                empty_fields.add(field)

        if empty_fields:
            empty_by_template[tpl_name] = empty_fields

    return empty_by_template


def _process_notes(
    items: list[dict],
    model_configs: list[ModelConfigComplete],
    builder: AnkiBuilder,
    skip_empty_template_fields: bool = False,
    skip_individual_empty_cards: bool = False,
) -> tuple[int, set[str], int]:
    """Add notes from *items* to *builder*, collecting media references.

    Args:
        items: Raw note data dictionaries from the YAML.
        model_configs: List of model configuration dicts.
        builder: The ``AnkiBuilder`` instance to populate.
        skip_empty_template_fields: If True, skip notes that have empty fields
            required by their templates. If False, create cards with empty fields
            (with warnings).
        skip_individual_empty_cards: If True, skip only the specific cards/templates
            that have empty required fields, while still creating other cards from
            the same note. This takes precedence over skip_empty_template_fields.

    Returns:
        A tuple of *(notes_processed, all_media_refs, skipped_count)*.
    """
    model_fields_map: dict[str, list[str]] = {
        cfg["name"]: cfg["fields"] for cfg in model_configs
    }
    # Map model names to their configs for template analysis
    model_config_map: dict[str, ModelConfigComplete] = {
        cfg["name"]: cfg for cfg in model_configs
    }
    first_model_name: str = model_configs[0]["name"]
    all_media_refs: set[str] = set()
    skipped_count: int = 0

    for item in items:
        # Determine which model to use
        target_model_name = item.get("model", item.get("type", first_model_name))
        if not isinstance(target_model_name, str):
            target_model_name = str(target_model_name)

        if target_model_name not in model_fields_map:
            logger.warning(
                "Model '%s' not found. Available: %s. Defaulting to '%s'.",
                target_model_name,
                ", ".join(model_fields_map.keys()),
                first_model_name,
            )
            target_model_name = first_model_name

        fields = model_fields_map[target_model_name]
        model_config = model_config_map[target_model_name]

        # Case-insensitive field lookup
        item_lower = {k.lower(): v for k, v in item.items()}
        field_values = [str(item_lower.get(f.lower(), "")) for f in fields]

        # Check for empty required fields in templates
        empty_by_template = _get_empty_fields_for_templates(item, model_config, fields)

        # Get list of all template names for this model
        all_template_names = set()
        for tpl in model_config.get("templates", []):
            all_template_names.add(tpl.get("name", "Unnamed"))

        # Determine which templates to include based on empty fields
        templates_to_include: list[str] | None = None
        if skip_individual_empty_cards and empty_by_template:
            # Include only templates that don't have empty fields
            templates_to_include = []
            for tpl_name in all_template_names:
                if tpl_name not in empty_by_template:
                    templates_to_include.append(tpl_name)

            # If all templates have empty fields, skip the note entirely
            if not templates_to_include:
                note_ref = f"Note '{item.get('id', items.index(item) + 1)}'"
                logger.info(
                    "%s: Skipping note - all templates have empty required fields: %s",
                    note_ref,
                    ", ".join(
                        f"{tpl}: {', '.join(sorted(empty_fields))}"
                        for tpl, empty_fields in empty_by_template.items()
                    ),
                )
                skipped_count += 1
                continue

        # Handle empty fields based on skip flag (for logging only when not using individual skip)
        if empty_by_template:
            note_ref = f"Note '{item.get('id', items.index(item) + 1)}'"
            if skip_empty_template_fields and not skip_individual_empty_cards:
                # Skip this note entirely
                logger.info(
                    "%s: Skipping note due to empty required fields in templates: %s",
                    note_ref,
                    ", ".join(
                        f"{tpl}: {', '.join(sorted(fields))}"
                        for tpl, fields in empty_by_template.items()
                    ),
                )
                skipped_count += 1
                continue
            elif not skip_individual_empty_cards:
                # Log warnings but still create the card
                for tpl_name, empty_fields in empty_by_template.items():
                    logger.warning(
                        "%s: Template '%s' has empty required fields: %s - "
                        "Card will be created with empty fields",
                        note_ref,
                        tpl_name,
                        ", ".join(sorted(empty_fields)),
                    )
            else:
                # Log which individual cards are being skipped
                for tpl_name, empty_fields in empty_by_template.items():
                    logger.info(
                        "%s: Skipping card for template '%s' due to empty fields: %s",
                        note_ref,
                        tpl_name,
                        ", ".join(sorted(empty_fields)),
                    )

        # Collect media references
        for fv in field_values:
            all_media_refs.update(get_media_references(fv))

        # Tags
        tags_raw = item.get("tags", [])
        tags: list[str] = tags_raw if isinstance(tags_raw, list) else [str(tags_raw)]
        if "id" in item:
            tags.append(f"id::{item['id']}")

        builder.add_note(
            field_values,
            tags=tags,
            model_name=target_model_name,
            templates_to_include=templates_to_include,
        )

    return len(items) - skipped_count, all_media_refs, skipped_count


def _add_media(
    builder: AnkiBuilder,
    media_folder: Path | None,
    all_media_refs: set[str],
) -> tuple[int, list[str]]:
    """Discover, add, and validate media files.

    Args:
        builder: The ``AnkiBuilder`` instance.
        media_folder: Optional path to the media directory.
        all_media_refs: Set of media filenames referenced in notes.

    Returns:
        A tuple of *(media_count, missing_refs)*.
    """
    if not media_folder:
        if all_media_refs:
            logger.warning(
                "Found %d media references but no media directory specified.",
                len(all_media_refs),
            )
        return 0, []

    discovered = discover_media_files(media_folder)
    for mf in discovered:
        builder.add_media(mf)

    missing: list[str] = []
    for ref in all_media_refs:
        try:
            validate_media_file(media_folder / ref)
        except MediaMissingError:
            missing.append(ref)

    return len(discovered), missing


def build_deck(
    deck_path: str | Path,
    output_path: str | Path = "deck.apkg",
    deck_name_override: str | None = None,
    media_dir_override: str | Path | None = None,
    skip_individual_empty_cards: bool = False,
) -> BuildResult:
    """Build an ``.apkg`` file from a YAML deck file.

    This function encapsulates the full build pipeline: loading the YAML,
    processing notes, handling media, and writing the ``.apkg`` output.

    Args:
        deck_path: Path to the YAML deck file.
        output_path: Destination path for the ``.apkg`` file.
        deck_name_override: Optional name override for the deck.
        media_dir_override: Optional media directory override.
        skip_individual_empty_cards: If True, skip only specific cards/templates
            that have empty required fields, while still creating other cards from
            the same note. For example, if "Lectura alternativa" is empty, the
            card "Numeral arábigo -> Lectura alternativa" will be skipped but
            other cards from the same note will still be created.

    Returns:
        A :class:`BuildResult` with details of the build.

    Raises:
        ConfigValidationError: If the YAML config section is invalid.
        DataValidationError: If the YAML data section is invalid.
        DeckBuildError: If the build process itself fails.
    """
    deck_path = Path(deck_path)
    output_path = Path(output_path)

    logger.info("Loading deck file: %s", deck_path)
    model_config, items, file_deck_name, file_media_dir = load_deck_file(deck_path)
    model_configs = cast(list[ModelConfigComplete], [model_config])

    final_deck_name = _resolve_deck_name(deck_name_override, file_deck_name, deck_path)

    media_folder: Path | None = (
        Path(media_dir_override) if media_dir_override else file_media_dir
    )

    logger.info("Building deck '%s' → %s", final_deck_name, output_path)
    builder = AnkiBuilder(final_deck_name, model_configs, media_folder)

    notes_processed, all_media_refs, skipped_count = _process_notes(
        items,
        model_configs,
        builder,
        skip_empty_template_fields=False,
        skip_individual_empty_cards=skip_individual_empty_cards,
    )
    media_count, missing_refs = _add_media(builder, media_folder, all_media_refs)

    builder.write_to_file(output_path)
    logger.info(
        "Built successfully: %d notes (%d skipped), %d media files",
        notes_processed,
        skipped_count,
        media_count,
    )

    return BuildResult(
        output_path=output_path,
        deck_name=final_deck_name,
        notes_processed=notes_processed,
        media_files=media_count,
        missing_media_refs=missing_refs,
    )


def validate_deck(
    deck_path: str | Path,
    strict: bool = False,
) -> ValidationResult:
    """Validate a YAML deck file without building it.

    Performs schema validation, checks for duplicate IDs, validates note
    fields, and runs basic HTML validation on field contents.

    Args:
        deck_path: Path to the YAML deck file.
        strict: If ``True``, treat warnings as errors.

    Returns:
        A :class:`ValidationResult` containing all found issues.

    Raises:
        ConfigValidationError: If the YAML config section is invalid.
        DataValidationError: If the YAML data section is invalid.
    """
    deck_path = Path(deck_path)
    result = ValidationResult()

    logger.info("Validating file: %s (strict=%s)", deck_path, strict)

    model_config, items, _, _ = load_deck_file(deck_path)
    model_configs = [model_config]

    model_names: set[str] = {cfg["name"] for cfg in model_configs}
    model_fields_map: dict[str, list[str]] = {
        cfg["name"]: cfg["fields"] for cfg in model_configs
    }
    first_model_name: str = model_configs[0]["name"]

    # Duplicate IDs
    duplicates = check_duplicate_ids(items)
    for id_, count in duplicates.items():
        result.issues.append(
            ValidationIssue("warning", f"Duplicate ID '{id_}' appears {count} times")
        )

    # Per-note validation
    for i, item in enumerate(items):
        note_ref = f"Note #{i + 1}"
        if "id" in item:
            note_ref += f" (ID: {item['id']})"

        # Model existence
        raw_model = item.get("model", item.get("type", first_model_name))
        target_model = raw_model if isinstance(raw_model, str) else str(raw_model)

        if target_model not in model_names:
            result.issues.append(
                ValidationIssue(
                    "error",
                    f"{note_ref}: Model '{target_model}' not found.",
                )
            )
            continue

        # Field presence
        fields = model_fields_map[target_model]
        _is_valid, missing = validate_note_fields(item, fields, validate_missing="warn")
        if missing:
            result.issues.append(
                ValidationIssue(
                    "warning",
                    f"{note_ref}: Missing fields: {', '.join(missing)}",
                )
            )

        # HTML validation
        for field_name in fields:
            content = str(item.get(field_name.lower(), ""))
            html_warnings = validate_html_tags(content)
            for warning in html_warnings:
                result.issues.append(
                    ValidationIssue(
                        "warning",
                        f"{note_ref}, field '{field_name}': {warning}",
                    )
                )

    logger.info(
        "Validation complete: %d issues (%d errors, %d warnings)",
        len(result.issues),
        sum(1 for i in result.issues if i.level == "error"),
        sum(1 for i in result.issues if i.level == "warning"),
    )
    return result


def push_apkg(
    apkg_path: str | Path,
    connector: AnkiAdapter,
    *,
    sync: bool = False,
) -> None:
    """Import an ``.apkg`` file into Anki.

    Extracts media files from the package and stores them via
    ``AnkiConnect`` before importing the package itself.

    Args:
        apkg_path: Path to the ``.apkg`` file.
        connector: An :class:`AnkiAdapter` implementation.
        sync: Whether to trigger an AnkiWeb sync after import.

    Raises:
        FileNotFoundError: If the ``.apkg`` file doesn't exist.
        AnkiConnectError: If the communication with Anki fails.
    """
    apkg_path = Path(apkg_path)
    logger.info("Pushing %s to Anki...", apkg_path)

    # Extract and store media from apkg
    with zipfile.ZipFile(apkg_path, "r") as zf:
        if "media" in zf.namelist():
            media_map: dict[str, str] = json.loads(zf.read("media").decode("utf-8"))
            if media_map:
                logger.info("Storing %d media files", len(media_map))
                for idx, filename in media_map.items():
                    try:
                        content = zf.read(idx)
                        encoded = base64.b64encode(content).decode("utf-8")
                        connector.invoke(
                            "storeMediaFile", filename=filename, data=encoded
                        )  # type: ignore[attr-defined]
                        logger.debug("Stored media: %s", filename)
                    except KeyError:
                        logger.warning("Media file %s not found in apkg", idx)
                    except Exception as e:
                        logger.warning("Failed to store %s: %s", filename, e)

    # Import
    connector.import_package(apkg_path)
    logger.info("Package imported successfully")

    if sync:
        logger.info("Syncing with AnkiWeb...")
        connector.sync()
