"""Tests for the media file handling module."""

from pathlib import Path

import pytest

from anki_yaml_tool.core.exceptions import MediaMissingError
from anki_yaml_tool.core.media import (
    discover_media_files,
    get_media_references,
    validate_media_file,
    validate_media_references,
)


def test_validate_media_file_success(tmp_path):
    """Test validating an existing media file."""
    media_file = tmp_path / "image.jpg"
    media_file.write_bytes(b"fake image data")

    result = validate_media_file(media_file)

    assert result == media_file
    assert result.exists()


def test_validate_media_file_nonexistent():
    """Test validating a nonexistent media file."""
    with pytest.raises(MediaMissingError) as exc_info:
        validate_media_file(Path("/nonexistent/image.jpg"))

    assert "not found" in str(exc_info.value).lower()


def test_validate_media_file_not_a_file(tmp_path):
    """Test validating a path that is not a file."""
    directory = tmp_path / "not_a_file"
    directory.mkdir()

    with pytest.raises(MediaMissingError) as exc_info:
        validate_media_file(directory)

    assert "not a file" in str(exc_info.value).lower()


def test_validate_media_file_with_string_path(tmp_path):
    """Test validating a media file using a string path."""
    media_file = tmp_path / "image.jpg"
    media_file.write_bytes(b"fake image data")

    result = validate_media_file(str(media_file))

    assert result == media_file


def test_discover_media_files_default_extensions(tmp_path):
    """Test discovering media files with default extensions."""
    # Create various media files
    (tmp_path / "image1.jpg").write_bytes(b"fake")
    (tmp_path / "image2.png").write_bytes(b"fake")
    (tmp_path / "audio.mp3").write_bytes(b"fake")
    (tmp_path / "video.mp4").write_bytes(b"fake")
    (tmp_path / "document.txt").write_bytes(b"fake")  # Not a media file

    media_files = discover_media_files(tmp_path)

    assert len(media_files) == 4  # Should not include .txt
    filenames = [f.name for f in media_files]
    assert "image1.jpg" in filenames
    assert "image2.png" in filenames
    assert "audio.mp3" in filenames
    assert "video.mp4" in filenames
    assert "document.txt" not in filenames


def test_discover_media_files_custom_extensions(tmp_path):
    """Test discovering media files with custom extensions."""
    (tmp_path / "image1.jpg").write_bytes(b"fake")
    (tmp_path / "image2.png").write_bytes(b"fake")
    (tmp_path / "audio.mp3").write_bytes(b"fake")

    media_files = discover_media_files(tmp_path, extensions=[".jpg", ".png"])

    assert len(media_files) == 2
    filenames = [f.name for f in media_files]
    assert "image1.jpg" in filenames
    assert "image2.png" in filenames
    assert "audio.mp3" not in filenames


def test_discover_media_files_case_insensitive(tmp_path):
    """Test that file discovery is case-insensitive."""
    (tmp_path / "image1.JPG").write_bytes(b"fake")
    (tmp_path / "image2.jpg").write_bytes(b"fake")

    media_files = discover_media_files(tmp_path, extensions=[".jpg"])

    assert len(media_files) == 2


def test_discover_media_files_nonexistent_directory():
    """Test discovering files in a nonexistent directory."""
    with pytest.raises(FileNotFoundError):
        discover_media_files(Path("/nonexistent/directory"))


def test_discover_media_files_not_a_directory(tmp_path):
    """Test discovering files when path is not a directory."""
    file_path = tmp_path / "not_a_dir.txt"
    file_path.write_text("content")

    with pytest.raises(FileNotFoundError):
        discover_media_files(file_path)


def test_get_media_references_img_tags():
    """Test extracting media references from img tags."""
    text = """
    <div>
        <img src="image1.jpg" alt="test">
        <img src="image2.png">
    </div>
    """

    references = get_media_references(text)

    assert len(references) == 2
    assert "image1.jpg" in references
    assert "image2.png" in references


def test_get_media_references_audio_tags():
    """Test extracting media references from audio tags."""
    text = """
    <audio src="audio1.mp3" controls></audio>
    <audio src="audio2.wav"></audio>
    """

    references = get_media_references(text)

    assert len(references) == 2
    assert "audio1.mp3" in references
    assert "audio2.wav" in references


def test_get_media_references_sound_tags():
    """Test extracting media references from [sound:...] tags."""
    text = """
    Some text [sound:pronunciation.mp3] more text
    Another [sound:example.wav] here
    """

    references = get_media_references(text)

    assert len(references) == 2
    assert "pronunciation.mp3" in references
    assert "example.wav" in references


def test_get_media_references_mixed():
    """Test extracting media references from mixed tags."""
    text = """
    <img src="image.jpg">
    [sound:audio.mp3]
    <audio src="voice.wav"></audio>
    """

    references = get_media_references(text)

    assert len(references) == 3
    assert "image.jpg" in references
    assert "audio.mp3" in references
    assert "voice.wav" in references


def test_get_media_references_with_paths():
    """Test that only filenames are extracted, not full paths."""
    text = '<img src="path/to/image.jpg">'

    references = get_media_references(text)

    assert len(references) == 1
    assert references[0] == "image.jpg"


def test_get_media_references_empty_text():
    """Test extracting references from empty text."""
    references = get_media_references("")

    assert len(references) == 0


def test_validate_media_references_all_exist(tmp_path):
    """Test validating media references when all files exist."""
    (tmp_path / "image.jpg").write_bytes(b"fake")
    (tmp_path / "audio.mp3").write_bytes(b"fake")

    text = '<img src="image.jpg"> [sound:audio.mp3]'

    validated = validate_media_references(text, tmp_path)

    assert len(validated) == 2
    filenames = [f.name for f in validated]
    assert "image.jpg" in filenames
    assert "audio.mp3" in filenames


def test_validate_media_references_missing_files(tmp_path):
    """Test validating media references when files are missing."""
    (tmp_path / "image.jpg").write_bytes(b"fake")
    # audio.mp3 is not created

    text = '<img src="image.jpg"> [sound:audio.mp3]'

    with pytest.raises(MediaMissingError) as exc_info:
        validate_media_references(text, tmp_path, raise_on_missing=True)

    assert "audio.mp3" in str(exc_info.value)


def test_validate_media_references_no_raise(tmp_path):
    """Test validating media references without raising on missing files."""
    (tmp_path / "image.jpg").write_bytes(b"fake")
    # audio.mp3 is not created

    text = '<img src="image.jpg"> [sound:audio.mp3]'

    validated = validate_media_references(text, tmp_path, raise_on_missing=False)

    assert len(validated) == 1
    assert validated[0].name == "image.jpg"


def test_validate_media_references_no_references(tmp_path):
    """Test validating text with no media references."""
    text = "Just some plain text with no media"

    validated = validate_media_references(text, tmp_path)

    assert len(validated) == 0
