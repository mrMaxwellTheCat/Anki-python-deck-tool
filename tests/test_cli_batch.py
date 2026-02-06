"""Tests for batch processing functionality.

This module contains tests for the `batch-build` command and
the batch processing utilities.
"""

import pytest
import yaml
from anki_yaml_tool.cli import cli
from click.testing import CliRunner


@pytest.fixture
def runner():
    """Provide a Click CLI test runner."""
    return CliRunner()


@pytest.fixture
def sample_deck_content():
    """Return sample deck YAML content."""
    return {
        "config": {
            "name": "Test Model",
            "fields": ["Front", "Back"],
            "templates": [{"name": "Card 1", "qfmt": "{{Front}}", "afmt": "{{Back}}"}],
        },
        "data": [
            {"front": "Question 1", "back": "Answer 1"},
            {"front": "Question 2", "back": "Answer 2"},
        ],
    }


class TestBatchBuildCommand:
    """Tests for the batch-build command."""

    def test_batch_build_help(self, runner):
        """Test that batch-build command help is accessible."""
        result = runner.invoke(cli, ["batch-build", "--help"])
        assert result.exit_code == 0
        assert "Build multiple decks" in result.output
        assert "--files" in result.output
        assert "--merge" in result.output
        assert "--output-dir" in result.output

    def test_batch_build_in_cli_help(self, runner):
        """Test that batch-build appears in main CLI help."""
        result = runner.invoke(cli, ["--help"])
        assert result.exit_code == 0
        assert "batch-build" in result.output

    def test_batch_build_requires_source(self, runner):
        """Test that either --files or --input-dir is required."""
        result = runner.invoke(cli, ["batch-build"])
        assert result.exit_code != 0
        assert "Must specify either" in result.output or "input-dir" in result.output

    def test_batch_build_single_file(self, runner, tmp_path, sample_deck_content):
        """Test batch-build with a single file."""
        deck_file = tmp_path / "deck.yaml"
        deck_file.write_text(yaml.dump(sample_deck_content), encoding="utf-8")

        with runner.isolated_filesystem(temp_dir=tmp_path):
            result = runner.invoke(
                cli,
                ["batch-build", "-f", str(deck_file), "-o", str(tmp_path)],
            )

            assert result.exit_code == 0
            assert "Found 1 deck files" in result.output
            assert "Successfully built" in result.output

    def test_batch_build_multiple_files(self, runner, tmp_path, sample_deck_content):
        """Test batch-build with multiple files."""
        deck1 = tmp_path / "deck1.yaml"
        deck2 = tmp_path / "deck2.yaml"
        deck1.write_text(yaml.dump(sample_deck_content), encoding="utf-8")
        deck2.write_text(yaml.dump(sample_deck_content), encoding="utf-8")

        with runner.isolated_filesystem(temp_dir=tmp_path):
            result = runner.invoke(
                cli,
                [
                    "batch-build",
                    "-f",
                    str(deck1),
                    "-f",
                    str(deck2),
                    "-o",
                    str(tmp_path),
                ],
            )

            assert result.exit_code == 0
            assert "Found 2 deck files" in result.output
            assert "Successfully built 2/2" in result.output

    def test_batch_build_merge(self, runner, tmp_path, sample_deck_content):
        """Test batch-build with --merge flag."""
        deck1 = tmp_path / "vocab1.yaml"
        deck2 = tmp_path / "vocab2.yaml"
        deck1.write_text(yaml.dump(sample_deck_content), encoding="utf-8")
        deck2.write_text(yaml.dump(sample_deck_content), encoding="utf-8")

        with runner.isolated_filesystem(temp_dir=tmp_path):
            result = runner.invoke(
                cli,
                [
                    "batch-build",
                    "-f",
                    str(deck1),
                    "-f",
                    str(deck2),
                    "--merge",
                    "--deck-name",
                    "All Vocab",
                    "-o",
                    str(tmp_path),
                ],
            )

            assert result.exit_code == 0
            assert "Merging files" in result.output
            assert "4 notes" in result.output  # 2 notes per file
            assert (tmp_path / "All_Vocab.apkg").exists()

    def test_batch_build_no_matching_files(self, runner, tmp_path):
        """Test batch-build with no matching files."""
        with runner.isolated_filesystem(temp_dir=tmp_path):
            result = runner.invoke(
                cli,
                ["batch-build", "-f", "nonexistent/*.yaml"],
            )

            assert result.exit_code != 0
            assert "No files matched" in result.output


class TestBatchUtilities:
    """Tests for batch processing utilities."""

    def test_expand_single_file(self, tmp_path):
        """Test expanding a single file path."""
        from anki_yaml_tool.core.batch import expand_file_patterns

        test_file = tmp_path / "test.yaml"
        test_file.write_text("content")

        result = expand_file_patterns((str(test_file),))
        assert len(result) == 1
        assert result[0] == test_file.resolve()

    def test_expand_glob_pattern(self, tmp_path):
        """Test expanding a glob pattern."""
        from anki_yaml_tool.core.batch import expand_file_patterns

        (tmp_path / "file1.yaml").write_text("content")
        (tmp_path / "file2.yaml").write_text("content")
        (tmp_path / "other.txt").write_text("content")

        result = expand_file_patterns((str(tmp_path / "*.yaml"),))
        assert len(result) == 2
        assert all(p.suffix == ".yaml" for p in result)

    def test_scan_directory_for_decks(self, tmp_path):
        """Test scanning directory for deck files."""
        from anki_yaml_tool.core.batch import scan_directory_for_decks

        # Create nested structure
        (tmp_path / "project1").mkdir()
        (tmp_path / "project1" / "deck.yaml").write_text("content")
        (tmp_path / "project2").mkdir()
        (tmp_path / "project2" / "deck.yaml").write_text("content")

        decks = list(scan_directory_for_decks(tmp_path))
        assert len(decks) == 2

    def test_get_deck_name_from_path(self, tmp_path):
        """Test generating deck name from path."""
        from anki_yaml_tool.core.batch import get_deck_name_from_path

        file_path = tmp_path / "spanish" / "deck.yaml"
        file_path.parent.mkdir()
        file_path.write_text("content")

        name = get_deck_name_from_path(file_path)
        assert name == "spanish"

    def test_get_deck_name_hierarchical(self, tmp_path):
        """Test generating hierarchical deck name."""
        from anki_yaml_tool.core.batch import get_deck_name_from_path

        file_path = tmp_path / "languages" / "spanish" / "deck.yaml"
        file_path.parent.mkdir(parents=True)
        file_path.write_text("content")

        name = get_deck_name_from_path(file_path, base_dir=tmp_path)
        assert name == "languages::spanish"
