"""Tests for the AnkiBuilder class."""

import pytest

from anki_yaml_tool.core.builder import AnkiBuilder
from anki_yaml_tool.core.exceptions import DeckBuildError


def test_stable_id_consistency():
    """Test that stable_id generates consistent IDs for the same input."""
    name = "Test Deck"
    id1 = AnkiBuilder.stable_id(name)
    id2 = AnkiBuilder.stable_id(name)
    assert id1 == id2, "stable_id should return the same ID for the same name"


def test_stable_id_uniqueness():
    """Test that stable_id generates different IDs for different inputs."""
    id1 = AnkiBuilder.stable_id("Deck A")
    id2 = AnkiBuilder.stable_id("Deck B")
    assert id1 != id2, "stable_id should return different IDs for different names"


def test_builder_initialization():
    """Test that AnkiBuilder initializes correctly with valid config."""
    config = {
        "name": "Test Model",
        "fields": ["Front", "Back"],
        "templates": [
            {
                "name": "Card 1",
                "qfmt": "{{Front}}",
                "afmt": "{{FrontSide}}<hr id=answer>{{Back}}",
            }
        ],
        "css": ".card { font-family: arial; }",
    }
    builder = AnkiBuilder("Test Deck", [config])
    assert builder.deck_name == "Test Deck"
    assert "Test Model" in builder.models
    assert builder.deck is not None


def test_builder_invalid_config():
    """Test that AnkiBuilder raises error with invalid config."""
    # Missing required 'fields' and 'templates' keys
    invalid_config = {"name": "Test Model"}
    with pytest.raises(DeckBuildError):
        AnkiBuilder("Test Deck", [invalid_config])


def test_add_note():
    """Test adding a note to the deck."""
    config = {
        "name": "Test Model",
        "fields": ["Front", "Back"],
        "templates": [
            {
                "name": "Card 1",
                "qfmt": "{{Front}}",
                "afmt": "{{FrontSide}}<hr id=answer>{{Back}}",
            }
        ],
    }
    builder = AnkiBuilder("Test Deck", [config])
    builder.add_note(["Question", "Answer"], tags=["test"])

    assert len(builder.deck.notes) == 1
    assert builder.deck.notes[0].fields == ["Question", "Answer"]
    assert "test" in builder.deck.notes[0].tags


def test_add_note_without_tags():
    """Test adding a note without tags."""
    config = {
        "name": "Test Model",
        "fields": ["Front", "Back"],
        "templates": [
            {
                "name": "Card 1",
                "qfmt": "{{Front}}",
                "afmt": "{{FrontSide}}<hr id=answer>{{Back}}",
            }
        ],
    }
    builder = AnkiBuilder("Test Deck", [config])
    builder.add_note(["Question", "Answer"])

    assert len(builder.deck.notes) == 1
    assert builder.deck.notes[0].tags == []


def test_write_to_file(tmp_path):
    """Test writing the deck to a file."""
    config = {
        "name": "Test Model",
        "fields": ["Front", "Back"],
        "templates": [
            {
                "name": "Card 1",
                "qfmt": "{{Front}}",
                "afmt": "{{FrontSide}}<hr id=answer>{{Back}}",
            }
        ],
    }
    builder = AnkiBuilder("Test Deck", [config])
    builder.add_note(["Question", "Answer"])

    output_path = tmp_path / "test_deck.apkg"
    builder.write_to_file(output_path)

    assert output_path.exists()
    assert output_path.stat().st_size > 0


def test_add_media(tmp_path):
    """Test adding media files to the deck."""
    config = {
        "name": "Test Model",
        "fields": ["Front", "Back"],
        "templates": [
            {
                "name": "Card 1",
                "qfmt": "{{Front}}",
                "afmt": "{{FrontSide}}<hr id=answer>{{Back}}",
            }
        ],
    }
    builder = AnkiBuilder("Test Deck", [config])

    # Create a dummy media file
    media_file = tmp_path / "test_image.jpg"
    media_file.write_text("fake image content")

    builder.add_media(media_file)
    assert len(builder.media_files) == 1
    assert str(media_file.absolute()) in builder.media_files


def test_add_media_nonexistent_file(tmp_path):
    """Test that add_media ignores nonexistent files."""
    config = {
        "name": "Test Model",
        "fields": ["Front", "Back"],
        "templates": [
            {
                "name": "Card 1",
                "qfmt": "{{Front}}",
                "afmt": "{{FrontSide}}<hr id=answer>{{Back}}",
            }
        ],
    }
    builder = AnkiBuilder("Test Deck", [config])

    nonexistent_file = tmp_path / "does_not_exist.jpg"
    builder.add_media(nonexistent_file)

    assert len(builder.media_files) == 0


def test_builder_multiple_models():
    """Test AnkiBuilder with multiple model configurations."""
    config1 = {
        "name": "Model 1",
        "fields": ["F1", "F2"],
        "templates": [{"name": "T1", "qfmt": "{{F1}}", "afmt": "{{F2}}"}],
    }
    config2 = {
        "name": "Model 2",
        "fields": ["FieldA", "FieldB", "FieldC"],
        "templates": [{"name": "T2", "qfmt": "{{FieldA}}", "afmt": "{{FieldB}}"}],
    }

    builder = AnkiBuilder("Multi Deck", [config1, config2])

    assert len(builder.models) == 2
    assert "Model 1" in builder.models
    assert "Model 2" in builder.models

    # Add note with Model 1 (implicit)
    builder.add_note(["V1", "V2"])
    assert builder.deck.notes[0].model.name == "Model 1"

    # Add note with Model 2 (explicit)
    builder.add_note(["VA", "VB", "VC"], model_name="Model 2")
    assert builder.deck.notes[1].model.name == "Model 2"

    # Add note with non-existent model
    with pytest.raises(DeckBuildError, match="Model 'Unknown' not found"):
        builder.add_note(["X"], model_name="Unknown")
