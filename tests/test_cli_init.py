"""Tests for the init command.

This module contains tests for the `anki-yaml-tool init` command
that scaffolds new Anki deck projects.
"""

import pytest
import yaml
from anki_yaml_tool.cli import cli, init
from click.testing import CliRunner


@pytest.fixture
def runner():
    """Provide a Click CLI test runner."""
    return CliRunner()


class TestInitCommand:
    """Tests for the init command."""

    def test_init_help(self, runner):
        """Test that init command help is accessible."""
        result = runner.invoke(init, ["--help"])
        assert result.exit_code == 0
        assert "Initialize a new Anki deck project" in result.output
        assert "--template" in result.output
        assert "basic" in result.output
        assert "language-learning" in result.output
        assert "technical" in result.output

    def test_init_in_cli_help(self, runner):
        """Test that init command appears in main CLI help."""
        result = runner.invoke(cli, ["--help"])
        assert result.exit_code == 0
        assert "init" in result.output

    def test_init_creates_basic_project(self, runner, tmp_path):
        """Test that init creates a basic project structure."""
        with runner.isolated_filesystem(temp_dir=tmp_path):
            result = runner.invoke(cli, ["init", "test-project"])

            assert result.exit_code == 0
            assert "Created project 'test-project'" in result.output
            assert "basic" in result.output

            # Check directory structure
            from pathlib import Path

            project_path = Path("test-project")
            assert project_path.exists()
            assert (project_path / "deck.yaml").exists()
            assert (project_path / "media").exists()
            assert (project_path / "README.md").exists()

    def test_init_creates_valid_yaml(self, runner, tmp_path):
        """Test that init creates valid, parseable YAML."""
        with runner.isolated_filesystem(temp_dir=tmp_path):
            result = runner.invoke(cli, ["init", "yaml-test"])
            assert result.exit_code == 0

            from pathlib import Path

            deck_file = Path("yaml-test") / "deck.yaml"
            with open(deck_file, encoding="utf-8") as f:
                data = yaml.safe_load(f)

            assert "config" in data
            assert "data" in data
            assert "deck-name" in data["config"]
            assert isinstance(data["config"]["fields"], list)
            assert len(data["data"]) > 0

    def test_init_with_language_template(self, runner, tmp_path):
        """Test init with language-learning template."""
        with runner.isolated_filesystem(temp_dir=tmp_path):
            result = runner.invoke(
                cli, ["init", "vocab-project", "--template", "language-learning"]
            )

            assert result.exit_code == 0
            assert "language-learning" in result.output

            from pathlib import Path

            deck_file = Path("vocab-project") / "deck.yaml"
            with open(deck_file, encoding="utf-8") as f:
                data = yaml.safe_load(f)

            # Language template has specific fields
            fields = data["config"]["fields"]
            assert "Word" in fields
            assert "Translation" in fields

    def test_init_with_technical_template(self, runner, tmp_path):
        """Test init with technical template."""
        with runner.isolated_filesystem(temp_dir=tmp_path):
            result = runner.invoke(cli, ["init", "tech-project", "-t", "technical"])

            assert result.exit_code == 0
            assert "technical" in result.output

            from pathlib import Path

            deck_file = Path("tech-project") / "deck.yaml"
            with open(deck_file, encoding="utf-8") as f:
                data = yaml.safe_load(f)

            fields = data["config"]["fields"]
            assert "Concept" in fields
            assert "Definition" in fields

    def test_init_default_project_name(self, runner, tmp_path):
        """Test init with default project name."""
        with runner.isolated_filesystem(temp_dir=tmp_path):
            result = runner.invoke(cli, ["init"])

            assert result.exit_code == 0
            assert "my-anki-deck" in result.output

            from pathlib import Path

            assert Path("my-anki-deck").exists()

    def test_init_fails_on_existing_directory(self, runner, tmp_path):
        """Test that init fails if directory already exists."""
        with runner.isolated_filesystem(temp_dir=tmp_path):
            from pathlib import Path

            Path("existing").mkdir()

            result = runner.invoke(cli, ["init", "existing"])

            assert result.exit_code != 0
            assert "already exists" in result.output

    def test_init_force_overwrites(self, runner, tmp_path):
        """Test that --force overwrites existing directory."""
        with runner.isolated_filesystem(temp_dir=tmp_path):
            from pathlib import Path

            Path("existing").mkdir()
            (Path("existing") / "old-file.txt").write_text("old content")

            result = runner.invoke(cli, ["init", "existing", "--force"])

            assert result.exit_code == 0
            assert (Path("existing") / "deck.yaml").exists()

    def test_init_creates_readme(self, runner, tmp_path):
        """Test that README is created with correct content."""
        with runner.isolated_filesystem(temp_dir=tmp_path):
            result = runner.invoke(cli, ["init", "readme-test"])
            assert result.exit_code == 0

            from pathlib import Path

            readme = (Path("readme-test") / "README.md").read_text()
            assert "anki-yaml-tool" in readme
            assert "build" in readme
            assert "push" in readme


class TestTemplates:
    """Tests for template module."""

    def test_get_template_names(self):
        """Test that template names are returned."""
        from anki_yaml_tool.templates import get_template_names

        names = get_template_names()
        assert "basic" in names
        assert "language-learning" in names
        assert "technical" in names

    def test_get_template_basic(self):
        """Test getting basic template."""
        from anki_yaml_tool.templates import get_template

        template = get_template("basic")
        assert "config" in template
        assert "data" in template
        assert "deck_name" in template

    def test_get_template_invalid(self):
        """Test that invalid template raises KeyError."""
        from anki_yaml_tool.templates import get_template

        with pytest.raises(KeyError):
            get_template("nonexistent")

    def test_generate_readme(self):
        """Test README generation."""
        from anki_yaml_tool.templates import generate_readme

        readme = generate_readme("Test Deck")
        assert "Test Deck" in readme
        assert "anki-yaml-tool" in readme
