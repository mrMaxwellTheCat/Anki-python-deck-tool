"""Tests for configuration file support.

This module contains tests for the ConfigFile class and
config file loading utilities.
"""

import pytest
import yaml
from click.testing import CliRunner

from anki_yaml_tool.cli import cli


@pytest.fixture
def runner():
    """Provide a Click CLI test runner."""
    return CliRunner()


class TestConfigFile:
    """Tests for the ConfigFile class."""

    def test_config_file_init(self):
        """Test ConfigFile initialization."""
        from anki_yaml_tool.core.config_file import ConfigFile

        config = ConfigFile()
        assert config.config == {}
        assert config.loaded_from == []

    def test_load_empty_config(self, tmp_path):
        """Test loading when no config files exist."""
        from anki_yaml_tool.core.config_file import ConfigFile

        config = ConfigFile().load(tmp_path)
        assert config.config == {}

    def test_load_project_config(self, tmp_path):
        """Test loading project config file."""
        from anki_yaml_tool.core.config_file import ConfigFile

        config_file = tmp_path / ".anki-yaml-tool.yaml"
        config_file.write_text(
            yaml.dump({"defaults": {"output_dir": "build"}}),
            encoding="utf-8",
        )

        config = ConfigFile().load(tmp_path)
        assert config.get("defaults.output_dir") == "build"
        assert len(config.loaded_from) == 1

    def test_get_with_dot_notation(self, tmp_path):
        """Test getting nested values with dot notation."""
        from anki_yaml_tool.core.config_file import ConfigFile

        config_file = tmp_path / ".anki-yaml-tool.yaml"
        config_file.write_text(
            yaml.dump({"build": {"output": "custom.apkg", "verbose": True}}),
            encoding="utf-8",
        )

        config = ConfigFile().load(tmp_path)
        assert config.get("build.output") == "custom.apkg"
        assert config.get("build.verbose") is True
        assert config.get("build.nonexistent", "default") == "default"

    def test_get_profile(self, tmp_path):
        """Test loading a profile configuration."""
        from anki_yaml_tool.core.config_file import ConfigFile

        config_file = tmp_path / ".anki-yaml-tool.yaml"
        config_file.write_text(
            yaml.dump(
                {
                    "defaults": {"output_dir": "."},
                    "profiles": {
                        "dev": {"verbose": 2, "output_dir": "dev-build"},
                        "prod": {"quiet": True},
                    },
                }
            ),
            encoding="utf-8",
        )

        config = ConfigFile().load(tmp_path)

        # Dev profile
        dev_config = config.get_profile("dev")
        assert dev_config["verbose"] == 2
        assert dev_config.get("defaults", {}).get("output_dir") == "."
        assert dev_config["output_dir"] == "dev-build"

        # Prod profile
        prod_config = config.get_profile("prod")
        assert prod_config["quiet"] is True

        # Nonexistent profile returns base config
        base_config = config.get_profile("nonexistent")
        assert "profiles" not in base_config

    def test_merge_configs(self, tmp_path):
        """Test config merging with nested dictionaries."""
        from anki_yaml_tool.core.config_file import ConfigFile

        config_file = tmp_path / ".anki-yaml-tool.yaml"
        config_file.write_text(
            yaml.dump({"a": {"x": 1, "y": 2}, "b": 10}),
            encoding="utf-8",
        )

        config = ConfigFile().load(tmp_path)
        assert config.get("a.x") == 1
        assert config.get("a.y") == 2
        assert config.get("b") == 10


class TestConfigCLI:
    """Tests for config file integration with CLI."""

    def test_profile_flag_in_help(self, runner):
        """Test that --profile flag appears in help."""
        result = runner.invoke(cli, ["--help"])
        assert result.exit_code == 0
        assert "--profile" in result.output or "-p" in result.output

    def test_cli_with_profile(self, runner, tmp_path):
        """Test CLI with a profile specified."""
        # Create config file with profile
        config_file = tmp_path / ".anki-yaml-tool.yaml"
        config_file.write_text(
            yaml.dump(
                {
                    "profiles": {
                        "test": {"verbose": 1},
                    }
                }
            ),
            encoding="utf-8",
        )

        with runner.isolated_filesystem(temp_dir=tmp_path):
            result = runner.invoke(cli, ["--profile", "test", "--help"])
            assert result.exit_code == 0


class TestConfigTemplate:
    """Tests for config file template generation."""

    def test_generate_config_template(self):
        """Test generating config template."""
        from anki_yaml_tool.core.config_file import generate_config_template

        template = generate_config_template()
        assert ".anki-yaml-tool.yaml" in template
        assert "defaults:" in template
        assert "profiles:" in template
        assert "dev:" in template
        assert "prod:" in template

    def test_get_default_config(self):
        """Test getting default configuration."""
        from anki_yaml_tool.core.config_file import get_default_config

        defaults = get_default_config()
        assert "defaults" in defaults
        assert "profiles" in defaults
