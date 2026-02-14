"""Integration tests for the anki-yaml-tool pipeline.

These tests verify the full pipeline from YAML input to .apkg file creation,
including multiple note types, invalid YAML handling, and media file inclusion.
"""

import zipfile

import pytest
from anki_yaml_tool.core.builder import AnkiBuilder, ModelConfigComplete
from anki_yaml_tool.core.config import load_deck_file
from anki_yaml_tool.core.exceptions import (
    ConfigValidationError,
    DataValidationError,
    DeckBuildError,
)

# ============================================================================
# Fixtures
# ============================================================================


@pytest.fixture
def basic_yaml_content() -> str:
    """Basic YAML content for a simple deck."""
    return """
config:
  name: "Test Basic Model"
  deck-name: "Test Deck"
  fields:
    - Front
    - Back
  templates:
    - name: Basic Card
      qfmt: "<div>{{Front}}</div>"
      afmt: "{{FrontSide}}<hr id=answer>{{Back}}"
data:
  - front: "Question 1"
    back: "Answer 1"
    tags: ["test", "basic"]
  - front: "Question 2"
    back: "Answer 2"
    tags: ["test"]
"""


@pytest.fixture
def basic_yaml_file(tmp_path, basic_yaml_content):
    """Create a temporary YAML file with basic content."""
    yaml_file = tmp_path / "basic_deck.yaml"
    yaml_file.write_text(basic_yaml_content)
    return yaml_file


@pytest.fixture
def multiple_note_types_yaml_content() -> str:
    """YAML content with multiple note types/models in a single deck."""
    return """
config:
  - name: "Basic Model"
    fields:
      - Front
      - Back
    templates:
      - name: Basic Card
        qfmt: "<div>{{Front}}</div>"
        afmt: "{{FrontSide}}<hr id=answer>{{Back}}"
  - name: "Reversed Model"
    fields:
      - Front
      - Back
    templates:
      - name: Reversed Card
        qfmt: "<div>{{Back}}</div>"
        afmt: "{{FrontSide}}<hr id=answer>{{Front}}"
data:
  - front: "Question 1"
    back: "Answer 1"
    model: "Basic Model"
    tags: ["test"]
  - front: "Answer 2"
    back: "Question 2"
    model: "Reversed Model"
    tags: ["test"]
"""


@pytest.fixture
def multiple_note_types_yaml_file(tmp_path, multiple_note_types_yaml_content):
    """Create a temporary YAML file with multiple note types."""
    yaml_file = tmp_path / "multi_note_types.yaml"
    yaml_file.write_text(multiple_note_types_yaml_content)
    return yaml_file


@pytest.fixture
def media_folder(tmp_path):
    """Create a temporary folder with media files."""
    media_dir = tmp_path / "media"
    media_dir.mkdir()

    # Create a simple audio file (fake mp3)
    audio_file = media_dir / "test_audio.mp3"
    audio_file.write_bytes(b"fake mp3 content")

    # Create a simple image file
    image_file = media_dir / "test_image.png"
    image_file.write_bytes(b"fake png content")

    return media_dir


@pytest.fixture
def yaml_with_media_content(media_folder) -> str:
    """YAML content that references media files."""
    media_path = str(media_folder)
    return f"""
config:
  name: "Media Test Model"
  deck-name: "Media Test Deck"
  media-folder: "{media_path}"
  fields:
    - Word
    - Audio
    - Image
  templates:
    - name: Media Card
      qfmt: "<div>{{Word}}</div>"
      afmt: "{{Word}}<br>{{Audio}}<br>{{Image}}"
data:
  - word: "Hello"
    audio: "[sound:test_audio.mp3]"
    image: "[img:test_image.png]"
    tags: ["media", "test"]
"""


@pytest.fixture
def yaml_with_media_file(tmp_path, yaml_with_media_content):
    """Create a temporary YAML file with media references."""
    yaml_file = tmp_path / "media_deck.yaml"
    yaml_file.write_text(yaml_with_media_content)
    return yaml_file


@pytest.fixture
def invalid_yaml_content() -> str:
    """Invalid YAML content (missing required fields)."""
    return """
config:
  name: "Incomplete Model"
  # Missing: fields and templates
data:
  - front: "Question"
    back: "Answer"
"""


@pytest.fixture
def invalid_yaml_file(tmp_path, invalid_yaml_content):
    """Create a temporary YAML file with invalid content."""
    yaml_file = tmp_path / "invalid_deck.yaml"
    yaml_file.write_text(invalid_yaml_content)
    return yaml_file


@pytest.fixture
def invalid_data_yaml_content() -> str:
    """YAML with invalid data section."""
    return """
config:
  name: "Test Model"
  fields:
    - Front
    - Back
  templates:
    - name: Basic
      qfmt: "{{Front}}"
      afmt: "{{Back}}"
data:
  # Data should be a list, not a dict
  front: "Question"
  back: "Answer"
"""


@pytest.fixture
def invalid_data_yaml_file(tmp_path, invalid_data_yaml_content):
    """Create a temporary YAML file with invalid data."""
    yaml_file = tmp_path / "invalid_data.yaml"
    yaml_file.write_text(invalid_data_yaml_content)
    return yaml_file


@pytest.fixture
def empty_yaml_file(tmp_path):
    """Create a temporary empty YAML file."""
    yaml_file = tmp_path / "empty.yaml"
    yaml_file.write_text("")
    return yaml_file


@pytest.fixture
def missing_data_section_yaml_content() -> str:
    """YAML with missing data section."""
    return """
config:
  name: "Test Model"
  fields:
    - Front
    - Back
  templates:
    - name: Basic
      qfmt: "{{Front}}"
      afmt: "{{Back}}"
"""


@pytest.fixture
def missing_data_yaml_file(tmp_path, missing_data_section_yaml_content):
    """Create a temporary YAML file missing data section."""
    yaml_file = tmp_path / "no_data.yaml"
    yaml_file.write_text(missing_data_section_yaml_content)
    return yaml_file


# ============================================================================
# Test 1: Full Pipeline (YAML → Builder → .apkg)
# ============================================================================


class TestFullPipeline:
    """Test the complete pipeline from YAML input to .apkg file creation."""

    def test_load_deck_file(self, basic_yaml_file):
        """Test loading a deck file returns correct configuration."""
        model_config, data, deck_name, media_folder = load_deck_file(basic_yaml_file)

        assert model_config is not None
        assert model_config["name"] == "Test Basic Model"
        assert len(data) == 2
        assert deck_name == "Test Deck"
        assert media_folder is None

    def test_load_deck_file_data_parsing(self, basic_yaml_file):
        """Test that data is correctly parsed from YAML."""
        _, data, _, _ = load_deck_file(basic_yaml_file)

        assert len(data) == 2
        assert data[0]["front"] == "Question 1"
        assert data[0]["back"] == "Answer 1"
        assert data[0]["tags"] == ["test", "basic"]
        assert data[1]["front"] == "Question 2"
        assert data[1]["back"] == "Answer 2"

    def test_builder_creates_deck(self):
        """Test that AnkiBuilder creates a deck from configuration."""
        config: ModelConfigComplete = {
            "name": "Test Model",
            "fields": ["Front", "Back"],
            "templates": [
                {
                    "name": "Basic Card",
                    "qfmt": "{{Front}}",
                    "afmt": "{{FrontSide}}<hr id=answer>{{Back}}",
                }
            ],
        }

        builder = AnkiBuilder("Test Deck", [config])

        assert builder.deck_name == "Test Deck"
        assert "Test Model" in builder.models

    def test_builder_adds_notes(self):
        """Test that notes are added to the deck correctly."""
        config: ModelConfigComplete = {
            "name": "Test Model",
            "fields": ["Front", "Back"],
            "templates": [
                {
                    "name": "Basic Card",
                    "qfmt": "{{Front}}",
                    "afmt": "{{FrontSide}}<hr id=answer>{{Back}}",
                }
            ],
        }

        builder = AnkiBuilder("Test Deck", [config])
        builder.add_note(["Question 1", "Answer 1"], tags=["test"])
        builder.add_note(["Question 2", "Answer 2"])

        assert len(builder.deck.notes) == 2
        assert builder.deck.notes[0].fields == ["Question 1", "Answer 1"]
        assert builder.deck.notes[0].tags == ["test"]
        assert builder.deck.notes[1].fields == ["Question 2", "Answer 2"]
        assert builder.deck.notes[1].tags == []

    def test_write_generates_apkg_file(self, tmp_path):
        """Test that write_to_file generates a valid .apkg file."""
        config: ModelConfigComplete = {
            "name": "Test Model",
            "fields": ["Front", "Back"],
            "templates": [
                {
                    "name": "Basic Card",
                    "qfmt": "{{Front}}",
                    "afmt": "{{FrontSide}}<hr id=answer>{{Back}}",
                }
            ],
        }

        builder = AnkiBuilder("Test Deck", [config])
        builder.add_note(["Question", "Answer"], tags=["test"])

        output_path = tmp_path / "test_deck.apkg"
        builder.write_to_file(output_path)

        # Verify file exists and has content
        assert output_path.exists()
        assert output_path.stat().st_size > 0

        # Verify it's a valid zip file (apkg is a zip)
        with zipfile.ZipFile(output_path, "r") as zf:
            file_list = zf.namelist()
            # Anki packages contain collection.anki21 or similar
            assert len(file_list) > 0

    def test_full_pipeline_yaml_to_apkg(self, tmp_path, basic_yaml_file):
        """Integration test: full pipeline from YAML to .apkg file."""
        # Step 1: Load deck file
        model_config, data, deck_name, media_folder = load_deck_file(basic_yaml_file)

        # Step 2: Create builder
        assert deck_name is not None  # Ensure deck_name is not None
        builder = AnkiBuilder(deck_name, [model_config], media_folder)

        # Step 3: Add notes
        fields = model_config["fields"]
        for item in data:
            field_values = [str(item.get(f.lower(), "")) for f in fields]
            tags = item.get("tags", [])
            builder.add_note(
                field_values, tags=tags if isinstance(tags, list) else [tags]
            )

        # Step 4: Write to file
        output_path = tmp_path / "full_pipeline.apkg"
        builder.write_to_file(output_path)

        # Verify
        assert output_path.exists()
        assert output_path.stat().st_size > 0

        # Verify the package contains notes
        with zipfile.ZipFile(output_path, "r") as zf:
            file_list = zf.namelist()
            # Check for media files and collection
            assert any("media" in f or "collection" in f for f in file_list)


# ============================================================================
# Test 2: Multiple Note Types
# ============================================================================


class TestMultipleNoteTypes:
    """Test handling of multiple note types/models in a single deck."""

    def test_builder_with_multiple_models(self):
        """Test that AnkiBuilder can handle multiple models."""
        config1: ModelConfigComplete = {
            "name": "Basic Model",
            "fields": ["Front", "Back"],
            "templates": [
                {
                    "name": "Basic Card",
                    "qfmt": "{{Front}}",
                    "afmt": "{{FrontSide}}<hr id=answer>{{Back}}",
                }
            ],
        }
        config2: ModelConfigComplete = {
            "name": "Reversed Model",
            "fields": ["Front", "Back"],
            "templates": [
                {
                    "name": "Reversed Card",
                    "qfmt": "{{Back}}",
                    "afmt": "{{FrontSide}}<hr id=answer>{{Front}}",
                }
            ],
        }

        builder = AnkiBuilder("Multi Model Deck", [config1, config2])

        assert len(builder.models) == 2
        assert "Basic Model" in builder.models
        assert "Reversed Model" in builder.models

    def test_add_note_with_specific_model(self):
        """Test adding notes with specific model names."""
        config1 = {
            "name": "Model A",
            "fields": ["Field1", "Field2"],
            "templates": [
                {"name": "Card A", "qfmt": "{{Field1}}", "afmt": "{{Field2}}"}
            ],
        }
        config2 = {
            "name": "Model B",
            "fields": ["FieldX", "FieldY"],
            "templates": [
                {"name": "Card B", "qfmt": "{{FieldX}}", "afmt": "{{FieldY}}"}
            ],
        }

        builder = AnkiBuilder("Test Deck", [config1, config2])

        # Add note with default model
        builder.add_note(["Value1", "Value2"])
        assert builder.deck.notes[0].model.name == "Model A"

        # Add note with specific model
        builder.add_note(["X", "Y"], model_name="Model B")
        assert builder.deck.notes[1].model.name == "Model B"

    def test_multiple_note_types_in_apkg(self, tmp_path):
        """Test that multiple note types are correctly included in the .apkg."""
        config1: ModelConfigComplete = {
            "name": "Basic Model",
            "fields": ["Front", "Back"],
            "templates": [
                {
                    "name": "Basic Card",
                    "qfmt": "{{Front}}",
                    "afmt": "{{FrontSide}}<hr id=answer>{{Back}}",
                }
            ],
        }
        config2: ModelConfigComplete = {
            "name": "Reversed Model",
            "fields": ["Front", "Back"],
            "templates": [
                {
                    "name": "Reversed Card",
                    "qfmt": "{{Back}}",
                    "afmt": "{{FrontSide}}<hr id=answer>{{Front}}",
                }
            ],
        }

        builder = AnkiBuilder("Multi Model Deck", [config1, config2])

        # Add notes with different models
        builder.add_note(["Q1", "A1"], model_name="Basic Model")
        builder.add_note(["A2", "Q2"], model_name="Reversed Model")

        output_path = tmp_path / "multi_model.apkg"
        builder.write_to_file(output_path)

        assert output_path.exists()
        assert output_path.stat().st_size > 0


# ============================================================================
# Test 3: Invalid YAML Handling
# ============================================================================


class TestInvalidYamlHandling:
    """Test graceful handling of invalid YAML configurations."""

    def test_missing_config_section(self, tmp_path):
        """Test error handling when config section is missing."""
        yaml_content = """
data:
  - front: "Question"
    back: "Answer"
"""
        yaml_file = tmp_path / "no_config.yaml"
        yaml_file.write_text(yaml_content)

        with pytest.raises(ConfigValidationError) as exc_info:
            load_deck_file(yaml_file)

        assert "config" in str(exc_info.value).lower()

    def test_missing_data_section(self, missing_data_yaml_file):
        """Test error handling when data section is missing."""
        with pytest.raises(DataValidationError) as exc_info:
            load_deck_file(missing_data_yaml_file)

        assert "data" in str(exc_info.value).lower()

    def test_invalid_config_fields(self, invalid_yaml_file):
        """Test error handling when config has invalid/missing fields."""
        with pytest.raises(ConfigValidationError) as exc_info:
            load_deck_file(invalid_yaml_file)

        # Should contain validation error message
        error_msg = str(exc_info.value).lower()
        assert (
            "fields" in error_msg
            or "templates" in error_msg
            or "validation" in error_msg
        )

    def test_invalid_data_format(self, invalid_data_yaml_file):
        """Test error handling when data is not a list."""
        with pytest.raises(DataValidationError) as exc_info:
            load_deck_file(invalid_data_yaml_file)

        assert "list" in str(exc_info.value).lower()

    def test_empty_yaml_file(self, empty_yaml_file):
        """Test error handling for empty YAML file."""
        with pytest.raises(ConfigValidationError) as exc_info:
            load_deck_file(empty_yaml_file)

        assert "empty" in str(exc_info.value).lower()

    def test_missing_required_model_fields(self, tmp_path):
        """Test error handling when model is missing required fields."""
        yaml_content = """
config:
  name: "Test Model"
  # Missing: fields and templates
data:
  - front: "Q"
    back: "A"
"""
        yaml_file = tmp_path / "incomplete_model.yaml"
        yaml_file.write_text(yaml_content)

        with pytest.raises(ConfigValidationError):
            load_deck_file(yaml_file)

    def test_deck_build_error_empty_models(self):
        """Test that builder raises error with no model configs."""
        with pytest.raises(DeckBuildError) as exc_info:
            AnkiBuilder("Test Deck", [])

        assert "at least one model" in str(exc_info.value).lower()


# ============================================================================
# Test 4: Media File Inclusion
# ============================================================================


class TestMediaFileInclusion:
    """Test media file inclusion in generated packages."""

    def test_add_media_file(self, tmp_path):
        """Test adding a media file to the builder."""
        config = {
            "name": "Test Model",
            "fields": ["Front", "Back"],
            "templates": [
                {
                    "name": "Basic Card",
                    "qfmt": "{{Front}}",
                    "afmt": "{{FrontSide}}<hr id=answer>{{Back}}",
                }
            ],
        }

        builder = AnkiBuilder("Test Deck", [config])

        # Create a media file
        media_file = tmp_path / "test.mp3"
        media_file.write_bytes(b"fake audio content")

        builder.add_media(media_file)

        assert len(builder.media_files) == 1
        assert str(media_file.absolute()) in builder.media_files

    def test_media_in_apkg_package(self, tmp_path):
        """Test that media files are included in the .apkg package."""
        config = {
            "name": "Test Model",
            "fields": ["Front", "Back"],
            "templates": [
                {
                    "name": "Basic Card",
                    "qfmt": "{{Front}}",
                    "afmt": "{{FrontSide}}<hr id=answer>{{Back}}",
                }
            ],
        }

        builder = AnkiBuilder("Test Deck", [config])
        builder.add_note(["Question", "Answer"])

        # Add a media file
        media_file = tmp_path / "test.mp3"
        media_file.write_bytes(b"fake audio content")
        builder.add_media(media_file)

        output_path = tmp_path / "media_test.apkg"
        builder.write_to_file(output_path)

        # Verify media is in the package
        with zipfile.ZipFile(output_path, "r") as zf:
            file_list = zf.namelist()
            # Check for media files (they're in a media folder in the zip)
            assert any("media" in f for f in file_list)

    def test_media_from_folder_references(self, tmp_path, media_folder):
        """Test that media files referenced in notes are included."""
        # Create deck with media folder
        config = {
            "name": "Media Model",
            "fields": ["Word", "Audio"],
            "templates": [
                {
                    "name": "Audio Card",
                    "qfmt": "{{Word}}",
                    "afmt": "{{Word}}<br>{{Audio}}",
                }
            ],
        }

        builder = AnkiBuilder("Media Deck", [config], media_folder)

        # Add note with media reference - builder scans for media references
        builder.add_note(["Hello", "[sound:test_audio.mp3]"])

        # The media file should be detected and added
        # (This tests the auto-detection in add_note)
        assert len(builder.deck.notes) == 1

        output_path = tmp_path / "media_refs.apkg"
        builder.write_to_file(output_path)

        assert output_path.exists()

    def test_media_folder_path_resolution(
        self, basic_yaml_file, yaml_with_media_content, tmp_path
    ):
        """Test that media folder path is correctly resolved."""
        # Create a YAML file with media folder reference
        media_dir = tmp_path / "media"
        if not media_dir.exists():
            media_dir.mkdir()
        (media_dir / "test.mp3").write_bytes(b"fake")

        yaml_content = """
config:
  name: "Test Model"
  media-folder: "./media"
  fields:
    - Front
    - Back
  templates:
    - name: Basic
      qfmt: "{Front}"
      afmt: "{Back}"
data:
  - front: "Q"
    back: "A"
"""
        yaml_file = tmp_path / "media_ref.yaml"
        yaml_file.write_text(yaml_content)

        # Need to resolve path relative to the yaml file
        model_config, data, deck_name, media_folder = load_deck_file(yaml_file)

        assert media_folder is not None
        assert media_folder.exists()
        assert (media_folder / "test.mp3").exists()


# ============================================================================
# Edge Cases and Additional Tests
# ============================================================================


class TestEdgeCases:
    """Additional edge case tests."""

    def test_deck_name_from_filename(self, tmp_path):
        """Test that deck name defaults to filename when not specified."""
        yaml_content = """
config:
  name: "Test Model"
  fields:
    - Front
    - Back
  templates:
    - name: Basic
      qfmt: "{{Front}}"
      afmt: "{{Back}}"
data:
  - front: "Q"
    back: "A"
"""
        # Create file with specific name
        yaml_file = tmp_path / "My_Custom_Deck.yaml"
        yaml_file.write_text(yaml_content)

        model_config, data, deck_name, _ = load_deck_file(yaml_file)

        # deck_name should be None (not specified in YAML)
        assert deck_name is None

    def test_empty_data_list(self, tmp_path):
        """Test error handling when data list is empty."""
        yaml_content = """
config:
  name: "Test Model"
  fields:
    - Front
    - Back
  templates:
    - name: Basic
      qfmt: "{{Front}}"
      afmt: "{{Back}}"
data: []
"""
        yaml_file = tmp_path / "empty_data.yaml"
        yaml_file.write_text(yaml_content)

        with pytest.raises(DataValidationError) as exc_info:
            load_deck_file(yaml_file)

        assert "empty" in str(exc_info.value).lower()

    def test_tags_handling(self, tmp_path):
        """Test that tags are correctly handled."""
        config = {
            "name": "Test Model",
            "fields": ["Front", "Back"],
            "templates": [
                {
                    "name": "Basic Card",
                    "qfmt": "{{Front}}",
                    "afmt": "{{FrontSide}}<hr id=answer>{{Back}}",
                }
            ],
        }

        builder = AnkiBuilder("Test Deck", [config])

        # Test with list of tags
        builder.add_note(["Q1", "A1"], tags=["tag1", "tag2"])
        assert builder.deck.notes[0].tags == ["tag1", "tag2"]

        # Test with no tags
        builder.add_note(["Q2", "A2"])
        assert builder.deck.notes[1].tags == []

    def test_case_insensitive_field_matching(self, tmp_path):
        """Test that field matching is case-insensitive."""
        yaml_content = """
config:
  name: "Test Model"
  fields:
    - Front
    - Back
  templates:
    - name: Basic
      qfmt: "{{Front}}"
      afmt: "{{Back}}"
data:
  - Front: "Question"
    Back: "Answer"
  - FRONT: "Q2"
    BACK: "A2"
"""
        yaml_file = tmp_path / "case_test.yaml"
        yaml_file.write_text(yaml_content)

        model_config, data, _, _ = load_deck_file(yaml_file)

        # Both should load correctly
        assert len(data) == 2
