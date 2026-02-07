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

    def test_batch_build_push_and_delete(
        self, runner, tmp_path, sample_deck_content, monkeypatch
    ):
        """Test batch-build with --push and --delete-after (mock AnkiConnector)."""
        deck_file = tmp_path / "vocab.yaml"
        deck_file.write_text(yaml.dump(sample_deck_content), encoding="utf-8")

        # Track calls to import_package
        calls: dict[str, int] = {"imported": 0}

        def fake_import_package(self, apkg_path):
            calls["imported"] += 1

        monkeypatch.setattr(
            "anki_yaml_tool.core.connector.AnkiConnector.import_package",
            fake_import_package,
        )

        with runner.isolated_filesystem(temp_dir=tmp_path):
            result = runner.invoke(
                cli,
                [
                    "batch-build",
                    "-f",
                    str(deck_file),
                    "-o",
                    str(tmp_path),
                    "--push",
                    "--delete-after",
                ],
            )

            assert result.exit_code == 0
            # Verify push summary and that push step ran
            assert (
                "built and pushed" in result.output
                or "built and pushed" in result.output.lower()
            )
            assert calls["imported"] == 1

            # Ensure output apkg was deleted after push
            apkg = tmp_path / f"{deck_file.stem}.apkg"
            assert not apkg.exists()

    def test_batch_build_push_with_media(self, runner, tmp_path, monkeypatch):
        """Test that media files are uploaded during batch push (storeMediaFile invoked)."""
        # Create deck content with media reference and media folder
        deck_content = {
            "config": {
                "name": "Test Model",
                "fields": ["Front", "Back"],
                "templates": [
                    {"name": "Card 1", "qfmt": "{{Front}}", "afmt": "{{Back}}"}
                ],
                "media-folder": "./media/",
            },
            "data": [{"front": "[img:image.jpg]", "back": "Answer"}],
        }

        deck_file = tmp_path / "deck.yaml"
        media_dir = tmp_path / "media"
        media_dir.mkdir()
        # Create a dummy media file
        (media_dir / "image.jpg").write_bytes(b"fake-image-data")
        deck_file.write_text(yaml.dump(deck_content), encoding="utf-8")

        calls: dict[str, int] = {"store": 0, "imported": 0}

        def fake_invoke(self, action, **params):
            if action == "storeMediaFile":
                calls["store"] += 1
                return None
            return None

        def fake_import_package(self, apkg_path):
            calls["imported"] += 1

        monkeypatch.setattr(
            "anki_yaml_tool.core.connector.AnkiConnector.invoke",
            fake_invoke,
        )
        monkeypatch.setattr(
            "anki_yaml_tool.core.connector.AnkiConnector.import_package",
            fake_import_package,
        )

        with runner.isolated_filesystem(temp_dir=tmp_path):
            result = runner.invoke(
                cli,
                [
                    "batch-build",
                    "-f",
                    str(deck_file),
                    "-o",
                    str(tmp_path),
                    "--push",
                    "--delete-after",
                ],
            )

            assert result.exit_code == 0
            assert calls["store"] >= 1
            assert calls["imported"] == 1

            # The output filename for input named 'deck.yaml' uses the parent
            # directory name. Verify that the generated .apkg (named after the
            # parent directory) has been deleted or remains based on push success.
            expected_name = f"{deck_file.parent.name}.apkg"
            apkg = tmp_path / expected_name
            assert not apkg.exists()

    def test_batch_build_push_failure(self, runner, tmp_path, monkeypatch):
        """Test behavior when Anki import fails during push (apkg should remain)."""
        deck_file = tmp_path / "deck.yaml"
        deck_file.write_text(
            yaml.dump(
                {
                    "config": {
                        "name": "Test Model",
                        "fields": ["Front", "Back"],
                        "templates": [
                            {"name": "Card 1", "qfmt": "{{Front}}", "afmt": "{{Back}}"}
                        ],
                    },
                    "data": [{"front": "Q", "back": "A"}],
                }
            ),
            encoding="utf-8",
        )

        def fake_import_package(self, apkg_path):
            raise Exception("import failed")

        monkeypatch.setattr(
            "anki_yaml_tool.core.connector.AnkiConnector.import_package",
            fake_import_package,
        )

        with runner.isolated_filesystem(temp_dir=tmp_path):
            result = runner.invoke(
                cli,
                [
                    "batch-build",
                    "-f",
                    str(deck_file),
                    "-o",
                    str(tmp_path),
                    "--push",
                    "--delete-after",
                ],
            )

            assert result.exit_code == 0
            assert "failed" in result.output.lower() or "failed" in result.output
            expected_name = f"{deck_file.parent.name}.apkg"
            apkg = tmp_path / expected_name
            # Ensure apkg remains because push failed
            assert apkg.exists()


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
