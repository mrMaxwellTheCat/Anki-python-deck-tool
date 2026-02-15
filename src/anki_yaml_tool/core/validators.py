"""Schema validation utilities using Pydantic.

This module provides validation functions for configuration
and data files, with detailed error messages.

The Pydantic models themselves live in :mod:`core.models`.
"""

from typing import Literal

from anki_yaml_tool.core.models import (  # noqa: F401 — re-exported
    DeckFileSchema,
    ModelConfigSchema,
    ModelTemplate,
    NoteData,
)


def validate_note_fields(
    note_data: dict,
    required_fields: list[str],
    validate_missing: Literal["error", "warn", "ignore"] = "warn",
    check_empty: bool = True,
) -> tuple[bool, list[str]]:
    """Validate that note data contains all required fields.

    Args:
        note_data: The note data dictionary.
        required_fields: List of required field names.
        validate_missing: How to handle missing fields:
            - "error": Return False if any fields are missing
            - "warn": Return True but include missing fields in the list
            - "ignore": Always return True with empty list
        check_empty: Whether to also check if required fields are empty.

    Returns:
        A tuple of (is_valid, missing_fields):
            - is_valid: True if validation passes, False otherwise
            - missing_fields: List of missing or empty field names
    """
    if validate_missing == "ignore":
        return True, []

    # Map keys to their original case for better error messages
    actual_keys = {k.lower(): k for k in note_data.keys()}
    required_lower = [f.lower() for f in required_fields]

    missing = []
    for field_lower in required_lower:
        if field_lower not in actual_keys:
            missing.append(field_lower)
        elif check_empty:
            value = note_data[actual_keys[field_lower]]
            if value is None or (isinstance(value, str) and not value.strip()):
                missing.append(field_lower)

    if validate_missing == "error" and missing:
        return False, missing

    return True, missing


def check_duplicate_ids(notes: list[dict]) -> dict[str, int]:
    """Check for duplicate note IDs in a list of notes.

    Args:
        notes: List of note data dictionaries.

    Returns:
        A dictionary mapping duplicate IDs to their occurrence count.
    """
    from collections import Counter

    # Extract IDs, filtering out None values
    ids: list[str] = [note["id"] for note in notes if note.get("id")]
    counts = Counter(ids)

    # Return only IDs that appear more than once
    return {id_: count for id_, count in counts.items() if count > 1}


def validate_html_tags(text: str, check_unclosed: bool = True) -> list[str]:
    """Perform basic HTML validation on text content.

    Args:
        text: The HTML text to validate.
        check_unclosed: Whether to check for unclosed tags.

    Returns:
        A list of validation warnings/errors found.
    """
    import re

    warnings: list[str] = []

    if check_unclosed:
        # HTML5 void elements - these don't need closing tags
        # Reference: https://html.spec.whatwg.org/multipage/syntax.html#elements-2
        void_elements = {
            "area",
            "base",
            "br",
            "col",
            "embed",
            "hr",
            "img",
            "input",
            "link",
            "meta",
            "param",
            "source",
            "track",
            "wbr",
            # Deprecated but still valid void elements
            "basefont",
            "frame",
            "keygen",
            "menuitem",
        }

        def _find_tag_end(tag_text: str, start_pos: int) -> int:
            """Find the closing > for a tag, handling > inside quotes."""
            i = start_pos
            in_single_quote = False
            in_double_quote = False

            while i < len(tag_text):
                char = tag_text[i]

                # Handle escape sequences
                if char == "\\" and i + 1 < len(tag_text):
                    i += 2
                    continue

                # Track quote state
                if char == "'" and not in_double_quote:
                    in_single_quote = not in_single_quote
                elif char == '"' and not in_single_quote:
                    in_double_quote = not in_double_quote
                elif char == ">" and not in_single_quote and not in_double_quote:
                    return i

                i += 1

            return -1  # No closing > found

        def _find_open_tags(html_text: str) -> list[str]:
            """Find opening tags that need closing, handling > in attributes."""
            open_tags = []
            i = 0

            while i < len(html_text):
                # Find next <
                tag_start = html_text.find("<", i)
                if tag_start == -1:
                    break

                # Check for closing tag or comment or CDATA
                if tag_start + 1 < len(html_text):
                    next_char = html_text[tag_start + 1]

                    # Skip closing tags
                    if next_char == "/":
                        tag_end = _find_tag_end(html_text, tag_start)
                        if tag_end == -1:
                            break
                        i = tag_end + 1
                        continue

                    # Skip comments <!-- -->
                    if html_text[tag_start : tag_start + 4] == "<!--":
                        comment_end = html_text.find("-->", tag_start + 4)
                        if comment_end == -1:
                            break
                        i = comment_end + 3
                        continue

                    # Skip CDATA <![CDATA[ ]]>
                    if html_text[tag_start : tag_start + 9] == "<![CDATA[":
                        cdata_end = html_text.find("]]>", tag_start + 9)
                        if cdata_end == -1:
                            break
                        i = cdata_end + 3
                        continue

                # Find the closing >
                tag_end = _find_tag_end(html_text, tag_start)
                if tag_end == -1:
                    break

                # Extract tag content
                tag_content = html_text[tag_start + 1 : tag_end]

                # Check if it's a closing tag
                if tag_content.startswith("/"):
                    i = tag_end + 1
                    continue

                # Parse tag name (first word)
                parts = tag_content.split()
                if not parts:
                    i = tag_end + 1
                    continue

                tag_name = parts[0]

                # Skip if empty or not a valid tag name
                if not tag_name or not tag_name.isalnum():
                    i = tag_end + 1
                    continue

                # Check if it's self-closing (/> at end) or void element
                tag_content_stripped = tag_content.strip()
                is_self_closing = tag_content_stripped.endswith("/")
                is_void = tag_name.lower() in void_elements

                if not is_self_closing and not is_void:
                    open_tags.append(tag_name)

                i = tag_end + 1

            return open_tags

        # Find closing tags
        close_tags = re.findall(r"</(\w+)>", text)

        # Find opening tags with proper handling of > in attributes
        open_tags = _find_open_tags(text)

        # Check if every opening tag has a corresponding closing tag
        from collections import Counter

        open_counts = Counter(open_tags)
        close_counts = Counter(close_tags)

        for tag, count in open_counts.items():
            if close_counts.get(tag, 0) < count:
                warnings.append(f"Unclosed tag: <{tag}>")

        for tag, count in close_counts.items():
            if open_counts.get(tag, 0) < count:
                warnings.append(f"Extra closing tag: </{tag}>")

    return warnings
