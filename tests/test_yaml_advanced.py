"""Tests for advanced YAML features."""

import os

import pytest
from anki_yaml_tool.core import yaml_advanced


class TestYAMLInclude:
    """Tests for YAML !include directive."""

    def test_include_file(self, tmp_path):
        """Test including an entire YAML file."""
        # Create included file
        included_file = tmp_path / "included.yaml"
        included_file.write_text("key: value\nlist:\n  - item1\n  - item2")

        # Create main file that includes it
        main_file = tmp_path / "main.yaml"
        main_file.write_text("data: !include included.yaml")

        # Load and verify
        result = yaml_advanced.load_yaml_advanced(main_file)
        assert result["data"]["key"] == "value"
        assert result["data"]["list"] == ["item1", "item2"]

    def test_include_specific_key(self, tmp_path):
        """Test including a specific key from a YAML file."""
        # Create included file with multiple keys
        included_file = tmp_path / "included.yaml"
        included_file.write_text("config:\n  name: test\ndata:\n  - item1")

        # Create main file that includes specific key
        main_file = tmp_path / "main.yaml"
        main_file.write_text("my_config: !include [included.yaml, config]")

        # Load and verify
        result = yaml_advanced.load_yaml_advanced(main_file)
        assert result["my_config"]["name"] == "test"

    def test_include_nonexistent_file(self, tmp_path):
        """Test that including a nonexistent file raises an error."""
        main_file = tmp_path / "main.yaml"
        main_file.write_text("data: !include nonexistent.yaml")

        with pytest.raises(yaml_advanced.YAMLIncludeError):
            yaml_advanced.load_yaml_advanced(main_file)

    def test_include_nested(self, tmp_path):
        """Test nested includes."""
        # Create deep nested file
        level3 = tmp_path / "level3.yaml"
        level3.write_text("value: deepest")

        level2 = tmp_path / "level2.yaml"
        level2.write_text("deep: !include level3.yaml")

        level1 = tmp_path / "level1.yaml"
        level1.write_text("nested: !include level2.yaml")

        main_file = tmp_path / "main.yaml"
        main_file.write_text("result: !include level1.yaml")

        result = yaml_advanced.load_yaml_advanced(main_file)
        assert result["result"]["nested"]["deep"]["value"] == "deepest"


class TestEnvironmentVariables:
    """Tests for environment variable substitution."""

    def test_env_var_dollar_brace(self, tmp_path):
        """Test ${VAR} syntax."""
        os.environ["TEST_VAR"] = "test_value"

        main_file = tmp_path / "main.yaml"
        main_file.write_text("value: ${TEST_VAR}")

        result = yaml_advanced.load_yaml_advanced(main_file)
        assert result["value"] == "test_value"

    def test_env_var_dollar(self, tmp_path):
        """Test $VAR syntax."""
        os.environ["TEST_VAR"] = "test_value"

        main_file = tmp_path / "main.yaml"
        main_file.write_text("value: $TEST_VAR")

        result = yaml_advanced.load_yaml_advanced(main_file)
        assert result["value"] == "test_value"

    def test_env_var_not_found(self, tmp_path):
        """Test that unknown vars are left as-is."""
        main_file = tmp_path / "main.yaml"
        main_file.write_text("value: $UNKNOWN_VAR_12345")

        result = yaml_advanced.load_yaml_advanced(main_file)
        assert result["value"] == "$UNKNOWN_VAR_12345"

    def test_env_var_in_nested(self, tmp_path):
        """Test env vars in nested structures."""
        os.environ["OUTER"] = "outer"
        os.environ["INNER"] = "inner"

        main_file = tmp_path / "main.yaml"
        main_file.write_text("outer:\n  inner: ${INNER}\nlist:\n  - $OUTER")

        result = yaml_advanced.load_yaml_advanced(main_file)
        assert result["outer"]["inner"] == "inner"
        assert result["list"][0] == "outer"


class TestJinjaTemplates:
    """Tests for Jinja2 template processing."""

    def test_simple_template(self, tmp_path):
        """Test simple template rendering."""
        main_file = tmp_path / "main.yaml"
        main_file.write_text("value: '{{ name }}'")

        result = yaml_advanced.load_yaml_advanced(
            main_file, jinja_context={"name": "World"}
        )
        assert result["value"] == "World"

    def test_template_in_dict_key(self, tmp_path):
        """Test template in dictionary key."""
        main_file = tmp_path / "main.yaml"
        main_file.write_text("'{{ prefix }}_key': value")

        result = yaml_advanced.load_yaml_advanced(
            main_file, jinja_context={"prefix": "my"}
        )
        assert "my_key" in result

    def test_template_with_loop(self, tmp_path):
        """Test template with loop."""
        main_file = tmp_path / "main.yaml"
        main_file.write_text("items: {% for i in items %}{{ i }},{% endfor %}")

        result = yaml_advanced.load_yaml_advanced(
            main_file, jinja_context={"items": [1, 2, 3]}
        )
        assert result["items"] == "1,2,3,"


class TestConditionalContent:
    """Tests for conditional content filtering."""

    def test_enabled_false(self, tmp_path):
        """Test that _enabled: false skips the item."""
        main_file = tmp_path / "main.yaml"
        main_file.write_text("- front: enabled\n- front: disabled\n  _enabled: false")

        result = yaml_advanced.load_yaml_advanced(main_file)
        assert len(result) == 1
        assert result[0]["front"] == "enabled"

    def test_tags_filter(self, tmp_path):
        """Test _tags filtering."""
        main_file = tmp_path / "main.yaml"
        main_file.write_text(
            "- front: dev_item\n  _tags: [dev]\n"
            "- front: prod_item\n  _tags: [prod]\n"
            "- front: both\n  _tags: [dev, prod]"
        )

        # Filter to only dev tags
        result = yaml_advanced.load_yaml_advanced(main_file, include_tags=["dev"])
        assert len(result) == 2
        fronts = [item["front"] for item in result]
        assert "dev_item" in fronts
        assert "both" in fronts
        assert "prod_item" not in fronts

    def test_enabled_flag_in_dict(self, tmp_path):
        """Test _enabled in dictionary context."""
        main_file = tmp_path / "main.yaml"
        main_file.write_text(
            "enabled_section:\n  content: yes\n"
            "disabled_section:\n  _enabled: false\n  content: no"
        )

        result = yaml_advanced.load_yaml_advanced(main_file)
        assert "enabled_section" in result
        assert "disabled_section" not in result


class TestYAMLAnchors:
    """Tests for YAML anchors and aliases."""

    def test_anchor_and_alias(self, tmp_path):
        """Test YAML anchor and alias expansion."""
        main_file = tmp_path / "main.yaml"
        main_file.write_text("base: &base 'shared value'\nfirst: *base\nsecond: *base")

        result = yaml_advanced.load_yaml_advanced(main_file)
        assert result["first"] == "shared value"
        assert result["second"] == "shared value"

    def test_anchor_in_list(self, tmp_path):
        """Test anchor in list context."""
        main_file = tmp_path / "main.yaml"
        main_file.write_text("items:\n  - &item {name: test, value: 100}\n  - *item")

        result = yaml_advanced.load_yaml_advanced(main_file)
        assert result["items"][1]["name"] == "test"
        assert result["items"][1]["value"] == 100


class TestLoadDeckAdvanced:
    """Tests for load_deck_advanced function."""

    def test_load_deck_file(self, tmp_path):
        """Test loading a complete deck file."""
        deck_file = tmp_path / "deck.yaml"
        deck_file.write_text(
            "deck-name: Test Deck\n"
            "config:\n"
            "  name: Basic\n"
            "  fields: [Front, Back]\n"
            "  templates:\n"
            "    - name: Card 1\n"
            "      qfmt: '{{Front}}'\n"
            "      afmt: '{{Front}}<hr>{{Back}}'\n"
            "data:\n"
            "  - front: q1\n"
            "    back: a1"
        )

        result = yaml_advanced.load_deck_advanced(deck_file)
        assert result["deck-name"] == "Test Deck"
        assert result["config"]["name"] == "Basic"
        assert len(result["data"]) == 1
