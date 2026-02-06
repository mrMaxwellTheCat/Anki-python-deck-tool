"""Tests for the validation module."""

import pytest
from pydantic import ValidationError

from anki_yaml_tool.core.validators import (
    ModelConfigSchema,
    ModelTemplate,
    NoteData,
    check_duplicate_ids,
    validate_html_tags,
    validate_note_fields,
)


def test_model_template_valid():
    """Test creating a valid model template."""
    template = ModelTemplate(
        name="Card 1", qfmt="{{Front}}", afmt="{{FrontSide}}<hr>{{Back}}"
    )

    assert template.name == "Card 1"
    assert template.qfmt == "{{Front}}"
    assert template.afmt == "{{FrontSide}}<hr>{{Back}}"


def test_model_template_strips_whitespace():
    """Test that whitespace is stripped from template fields."""
    template = ModelTemplate(
        name="  Card 1  ", qfmt="  {{Front}}  ", afmt="  {{Back}}  "
    )

    assert template.name == "Card 1"
    assert template.qfmt == "{{Front}}"
    assert template.afmt == "{{Back}}"


def test_model_template_empty_name():
    """Test that empty template name raises validation error."""
    with pytest.raises(ValidationError) as exc_info:
        ModelTemplate(name="", qfmt="{{Front}}", afmt="{{Back}}")

    assert "name" in str(exc_info.value).lower()


def test_model_config_valid():
    """Test creating a valid model configuration."""
    config = ModelConfigSchema(
        name="Test Model",
        fields=["Front", "Back"],
        templates=[
            ModelTemplate(
                name="Card 1", qfmt="{{Front}}", afmt="{{FrontSide}}<hr>{{Back}}"
            )
        ],
        css=".card { font-size: 20px; }",
    )

    assert config.name == "Test Model"
    assert config.fields == ["Front", "Back"]
    assert len(config.templates) == 1
    assert config.css == ".card { font-size: 20px; }"


def test_model_config_default_css():
    """Test that CSS defaults to empty string."""
    config = ModelConfigSchema(
        name="Test Model",
        fields=["Front"],
        templates=[ModelTemplate(name="Card 1", qfmt="{{Front}}", afmt="{{Back}}")],
    )

    assert config.css == ""


def test_model_config_empty_fields():
    """Test that empty fields list raises validation error."""
    with pytest.raises(ValidationError) as exc_info:
        ModelConfigSchema(
            name="Test Model",
            fields=[],
            templates=[ModelTemplate(name="Card 1", qfmt="{{Front}}", afmt="{{Back}}")],
        )

    assert "fields" in str(exc_info.value).lower()


def test_model_config_duplicate_fields():
    """Test that duplicate field names raise validation error."""
    with pytest.raises(ValidationError) as exc_info:
        ModelConfigSchema(
            name="Test Model",
            fields=["Front", "Back", "Front"],
            templates=[ModelTemplate(name="Card 1", qfmt="{{Front}}", afmt="{{Back}}")],
        )

    assert "unique" in str(exc_info.value).lower()


def test_model_config_empty_field_name():
    """Test that empty field names raise validation error."""
    with pytest.raises(ValidationError) as exc_info:
        ModelConfigSchema(
            name="Test Model",
            fields=["Front", "", "Back"],
            templates=[ModelTemplate(name="Card 1", qfmt="{{Front}}", afmt="{{Back}}")],
        )

    assert "empty" in str(exc_info.value).lower()


def test_model_config_empty_templates():
    """Test that empty templates list raises validation error."""
    with pytest.raises(ValidationError) as exc_info:
        ModelConfigSchema(name="Test Model", fields=["Front"], templates=[])

    assert "templates" in str(exc_info.value).lower()


def test_model_config_duplicate_template_names():
    """Test that duplicate template names raise validation error."""
    with pytest.raises(ValidationError) as exc_info:
        ModelConfigSchema(
            name="Test Model",
            fields=["Front"],
            templates=[
                ModelTemplate(name="Card 1", qfmt="{{Front}}", afmt="{{Back}}"),
                ModelTemplate(name="Card 1", qfmt="{{Front}}", afmt="{{Back}}"),
            ],
        )

    assert "unique" in str(exc_info.value).lower()


def test_note_data_valid():
    """Test creating valid note data."""
    note = NoteData(front="Question", back="Answer", tags=["tag1", "tag2"], id="note1")

    assert note.tags == ["tag1", "tag2"]
    assert note.id == "note1"


def test_note_data_default_tags():
    """Test that tags default to empty list."""
    note = NoteData()

    assert note.tags == []
    assert note.id is None


def test_note_data_string_tag_converted_to_list():
    """Test that a string tag is converted to a list."""
    note = NoteData(tags="single_tag")

    assert note.tags == ["single_tag"]


def test_note_data_strips_empty_tags():
    """Test that empty tags are filtered out."""
    note = NoteData(tags=["tag1", "", "tag2", None])

    assert note.tags == ["tag1", "tag2"]


def test_validate_note_fields_all_present():
    """Test validating note fields when all are present."""
    note_data = {"front": "Q", "back": "A", "tags": []}
    required = ["front", "back"]

    valid, missing = validate_note_fields(note_data, required, validate_missing="error")

    assert valid is True
    assert missing == []


def test_validate_note_fields_case_insensitive():
    """Test that field validation is case-insensitive."""
    note_data = {"Front": "Q", "BACK": "A"}
    required = ["front", "back"]

    valid, missing = validate_note_fields(note_data, required, validate_missing="error")

    assert valid is True
    assert missing == []


def test_validate_note_fields_missing_with_error():
    """Test validating note fields with missing field (error mode)."""
    note_data = {"front": "Q"}
    required = ["front", "back"]

    valid, missing = validate_note_fields(note_data, required, validate_missing="error")

    assert valid is False
    assert "back" in missing


def test_validate_note_fields_missing_with_warn():
    """Test validating note fields with missing field (warn mode)."""
    note_data = {"front": "Q"}
    required = ["front", "back"]

    valid, missing = validate_note_fields(note_data, required, validate_missing="warn")

    assert valid is True
    assert "back" in missing


def test_validate_note_fields_ignore_missing():
    """Test validating note fields with ignore mode."""
    note_data = {"front": "Q"}
    required = ["front", "back"]

    valid, missing = validate_note_fields(
        note_data, required, validate_missing="ignore"
    )

    assert valid is True
    assert missing == []


def test_validate_note_fields_empty_values():
    """Test validating note fields with empty values."""
    note_data = {"front": "Q", "back": ""}
    required = ["front", "back"]

    # With check_empty=True (default)
    valid, missing = validate_note_fields(note_data, required)
    assert "back" in missing

    # With check_empty=False
    valid, missing = validate_note_fields(note_data, required, check_empty=False)
    assert "back" not in missing


def test_check_duplicate_ids_none():
    """Test checking for duplicate IDs when there are none."""
    notes = [{"id": "1"}, {"id": "2"}, {"id": "3"}]

    duplicates = check_duplicate_ids(notes)

    assert duplicates == {}


def test_check_duplicate_ids_found():
    """Test checking for duplicate IDs when duplicates exist."""
    notes = [{"id": "1"}, {"id": "2"}, {"id": "1"}, {"id": "3"}, {"id": "2"}]

    duplicates = check_duplicate_ids(notes)

    assert duplicates == {"1": 2, "2": 2}


def test_check_duplicate_ids_no_ids():
    """Test checking for duplicate IDs when notes have no IDs."""
    notes = [{"front": "Q1"}, {"front": "Q2"}]

    duplicates = check_duplicate_ids(notes)

    assert duplicates == {}


def test_validate_html_tags_valid():
    """Test HTML validation with properly closed tags."""
    html = "<div><p>Text</p></div>"

    warnings = validate_html_tags(html)

    assert warnings == []


def test_validate_html_tags_unclosed():
    """Test HTML validation with unclosed tag."""
    html = "<div><p>Text</div>"

    warnings = validate_html_tags(html)

    assert len(warnings) > 0
    assert any("unclosed" in w.lower() for w in warnings)


def test_validate_html_tags_extra_closing():
    """Test HTML validation with extra closing tag."""
    html = "<div>Text</div></div>"

    warnings = validate_html_tags(html)

    assert len(warnings) > 0
    assert any("extra" in w.lower() for w in warnings)


def test_validate_html_tags_self_closing():
    """Test HTML validation ignores self-closing tags."""
    html = "<div><img src='test.jpg'><br></div>"

    warnings = validate_html_tags(html)

    assert warnings == []


def test_validate_html_tags_no_check():
    """Test HTML validation with check_unclosed=False."""
    html = "<div><p>Text</div>"  # Unclosed <p>

    warnings = validate_html_tags(html, check_unclosed=False)

    assert warnings == []
