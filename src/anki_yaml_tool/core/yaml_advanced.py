"""Advanced YAML processing features.

This module provides:
- YAML Includes (!include): Include fragments from other YAML files
- Variables & Templates: Jinja2 templating and environment variable substitution
- Conditional Content: Conditional inclusion based on tags or flags

Usage:
    from anki_yaml_tool.core.yaml_advanced import load_yaml_advanced

    # Load YAML with all advanced features enabled
    data = load_yaml_advanced("deck.yaml")
"""

import os
import re
from pathlib import Path
from typing import Any

import yaml
from yaml import nodes

# Try to import Jinja2, make it optional
try:
    from jinja2 import Template as JinjaTemplate

    JINJA2_AVAILABLE: bool = True
except ImportError:
    JINJA2_AVAILABLE = False
    JinjaTemplate = None


class YAMLIncludeError(Exception):
    """Exception raised for YAML include errors."""

    pass


class YAMLTemplateError(Exception):
    """Exception raised for YAML template errors."""

    pass


class YAMLConditionalError(Exception):
    """Exception raised for YAML conditional errors."""

    pass


# Global base directory for includes (set during loading)
_base_dir_global: Path | None = None


def _get_base_dir() -> Path:
    """Get the base directory for includes."""
    global _base_dir_global
    return _base_dir_global or Path.cwd()


def _set_base_dir(base_dir: Path) -> None:
    """Set the base directory for includes."""
    global _base_dir_global
    _base_dir_global = base_dir


def _resolve_include_path(path: str | list) -> tuple[Path, str | None]:
    """Resolve include path and optional key.

    Args:
        path: String path or list [path, key] or [path, {vars}]

    Returns:
        Tuple of (resolved_path, optional_key)
    """
    base_dir = _get_base_dir()

    if isinstance(path, list):
        file_path = path[0]
        key = path[1] if len(path) > 1 else None
        if isinstance(key, dict):
            # Variables passed with include - treat as no key
            key = None
        return (base_dir / file_path).resolve(), key
    return (base_dir / path).resolve(), None


def _load_include_file(path: str | list) -> Any:
    """Load an included YAML file.

    Args:
        path: Path to include or list [path, key]

    Returns:
        Loaded YAML data
    """
    resolved_path, key = _resolve_include_path(path)

    if not resolved_path.exists():
        raise YAMLIncludeError(f"Include file not found: {resolved_path}")

    # Recursively use advanced loading for included files
    included_data = load_yaml_advanced(resolved_path)

    if key is not None:
        if isinstance(included_data, dict) and key in included_data:
            return included_data[key]
        raise YAMLIncludeError(
            f"Key '{key}' not found in include file: {resolved_path}"
        )

    return included_data


def _include_constructor(loader: yaml.SafeLoader, node: nodes.Node) -> Any:
    """Constructor for !include directive."""
    if isinstance(node, nodes.ScalarNode):
        return _load_include_file(loader.construct_scalar(node))
    elif isinstance(node, nodes.SequenceNode):
        return _load_include_file(loader.construct_sequence(node))
    raise YAMLIncludeError("!include expects a path or [path, key]")


# Create custom loader class with !include support
class IncludeLoader(yaml.SafeLoader):
    """Custom YAML loader that supports !include directive.

    Usage in YAML:
        # Include entire file
        !include path/to/file.yaml

        # Include specific key from file
        !include [path/to/file.yaml, key]

        # Include with variables
        !include [path/to/file.yaml, {var1: value1, var2: value2}]
    """

    pass


IncludeLoader.add_constructor("!include", _include_constructor)


def substitute_env_vars(data: Any, pattern: str = r"\$\{(\w+)\}|\$(\w+)") -> Any:
    """Substitute environment variables in strings.

    Supports ${VAR} and $VAR syntax.

    Args:
        data: Data to process (can be str, list, dict, or nested)
        pattern: Regex pattern for variable substitution

    Returns:
        Data with environment variables substituted
    """
    if isinstance(data, str):
        # Substitute environment variables
        def replace_env_var(match: re.Match) -> str:
            var_name = match.group(1) or match.group(2)
            return os.environ.get(var_name, match.group(0))

        return re.sub(pattern, replace_env_var, data)

    elif isinstance(data, dict):
        return {k: substitute_env_vars(v, pattern) for k, v in data.items()}

    elif isinstance(data, list):
        return [substitute_env_vars(item, pattern) for item in data]

    return data


def process_jinja_templates(data: Any, context: dict[str, Any] | None = None) -> Any:
    """Process Jinja2-style templates in YAML data.

    Templates use {{ variable }} or {% template %} syntax.
    Only processes templates when context is provided or when the
    content explicitly looks like a Jinja2 template.

    Args:
        data: Data to process
        context: Context variables for templates

    Returns:
        Data with templates rendered
    """
    if not JINJA2_AVAILABLE or JinjaTemplate is None:
        return data

    context = context or {}
    # Only process if context is provided or we detect Jinja2 template syntax
    has_context = bool(context)

    if isinstance(data, str):
        # Check if string contains Jinja2 template syntax
        # Only process if we have context OR it's clearly a Jinja2 template
        if "{{" in data or "{%" in data:
            # If we have context, always process
            # Otherwise, check if it looks like a valid template
            if has_context or _looks_like_jinja_template(data):
                try:
                    template = JinjaTemplate(data, autoescape=False)
                    return template.render(**context)
                except Exception as e:
                    raise YAMLTemplateError(f"Template rendering error: {e}") from e
        return data

    elif isinstance(data, dict):
        result = {}
        for key, value in data.items():
            # Check for template variables in key
            if isinstance(key, str) and ("{{" in key or "{%" in key):
                if has_context or _looks_like_jinja_template(key):
                    try:
                        key = JinjaTemplate(key, autoescape=False).render(**context)
                    except Exception as e:
                        raise YAMLTemplateError(
                            f"Template rendering error in key: {e}"
                        ) from e
            result[key] = process_jinja_templates(value, context)
        return result

    elif isinstance(data, list):
        return [process_jinja_templates(item, context) for item in data]

    return data


def _looks_like_jinja_template(text: str) -> bool:
    """Check if text looks like a Jinja2 template rather than literal content.

    Jinja2 templates typically have:
    - Spaces around variables: {{ variable }}
    - Filters: {{ variable|filter }}
    - Tests: {{ value is defined }}
    - Block tags: {% if %}, {% for %}, etc.

    Anki templates like {{Front}} without spaces are not Jinja2.

    Args:
        text: Text to check

    Returns:
        True if it looks like a Jinja2 template
    """
    import re

    # Jinja2 tags: {% ... %}
    if re.search(r"\{%.*?%\}", text):
        return True

    # Jinja2 filters: {{ var|filter }}
    if re.search(r"\{\{\s*\w+\s*\|", text):
        return True

    # Jinja2 with spaces: {{ variable }} or {{ expression }}
    # Must have spaces or more complex expressions
    if re.search(r"\{\{\s+\S+\s+\}\}", text):
        return True

    # Jinja2 tests: {{ x is y }}, {{ x == y }}
    if re.search(r"\{\{.*?(?:is|==|!=|>|<|>=|<=|and|or|not|in)\.*\}\}", text):
        return True

    return False


def filter_conditional_content(
    data: Any,
    enabled_flag: str = "_enabled",
    tags_flag: str = "_tags",
    include_tags: list[str] | None = None,
) -> Any:
    """Filter content based on conditional flags.

    Supports:
    - _enabled: false to skip items
    - _tags: list of tags for conditional inclusion

    Args:
        data: Data to filter
        enabled_flag: Flag name for enabled status
        tags_flag: Flag name for tags
        include_tags: Tags to include (None = include all)

    Returns:
        Filtered data
    """
    if isinstance(data, dict):
        # Check if this item should be skipped
        if enabled_flag in data and data[enabled_flag] is False:
            return None

        # Check tags for conditional inclusion
        if tags_flag in data and include_tags is not None:
            item_tags = data[tags_flag]
            if isinstance(item_tags, list):
                # Include only if any tag matches
                if not any(tag in item_tags for tag in include_tags):
                    return None

        # Process nested content
        result = {}
        for key, value in data.items():
            # Skip internal flags in output
            if key in (enabled_flag, tags_flag):
                continue

            filtered = filter_conditional_content(
                value, enabled_flag, tags_flag, include_tags
            )
            if filtered is not None:
                result[key] = filtered
        return result

    elif isinstance(data, list):
        result = []
        for item in data:
            filtered = filter_conditional_content(
                item, enabled_flag, tags_flag, include_tags
            )
            if filtered is not None:
                result.append(filtered)
        return result

    return data


def expand_yaml_anchors(data: Any) -> Any:
    """Expand YAML anchors and aliases.

    PyYAML's safe_load already expands anchors/aliases,
    but this ensures they're properly handled.

    Args:
        data: Data with potential anchors

    Returns:
        Data with anchors expanded
    """
    # PyYAML safe_load already handles this, but we ensure
    # deep copies are made to avoid mutation issues
    if isinstance(data, dict):
        return {k: expand_yaml_anchors(v) for k, v in data.items()}
    elif isinstance(data, list):
        return [expand_yaml_anchors(item) for item in data]
    return data


def load_yaml_advanced(
    file_path: str | Path,
    base_dir: Path | None = None,
    env_vars: bool = True,
    jinja_templates: bool = True,
    jinja_context: dict[str, Any] | None = None,
    conditional: bool = True,
    include_tags: list[str] | None = None,
) -> Any:
    """Load YAML file with advanced processing features.

    Args:
        file_path: Path to the YAML file
        base_dir: Base directory for includes (defaults to file's directory)
        env_vars: Enable environment variable substitution
        jinja_templates: Enable Jinja2 template processing
        jinja_context: Additional context for Jinja2 templates
        conditional: Enable conditional content filtering
        include_tags: Tags to include for conditional filtering

    Returns:
        Processed YAML data

    Raises:
        YAMLIncludeError: If include fails
        YAMLTemplateError: If template rendering fails
        FileNotFoundError: If file doesn't exist
    """
    path = Path(file_path)

    if not path.exists():
        raise FileNotFoundError(f"YAML file not found: {file_path}")

    # Determine base directory for includes
    resolved_base_dir: Path
    if base_dir is None:
        resolved_base_dir = path.parent.resolve()
    else:
        resolved_base_dir = base_dir.resolve()

    # Set global base dir for include resolution
    global _base_dir_global
    old_base_dir = _base_dir_global
    try:
        _base_dir_global = resolved_base_dir

        # Load YAML with !include support
        with open(path, encoding="utf-8") as f:
            data = yaml.load(f, Loader=IncludeLoader)

        # Process environment variables
        if env_vars:
            data = substitute_env_vars(data)

        # Process Jinja2 templates
        if jinja_templates and JINJA2_AVAILABLE:
            data = process_jinja_templates(data, jinja_context)

        # Expand YAML anchors (already done by PyYAML, but ensure consistency)
        data = expand_yaml_anchors(data)

        # Filter conditional content
        if conditional:
            data = filter_conditional_content(data, include_tags=include_tags)

        return data
    finally:
        # Restore previous base dir
        _base_dir_global = old_base_dir


# Convenience function for loading deck files with advanced features
def load_deck_advanced(
    deck_path: str | Path,
    include_tags: list[str] | None = None,
    jinja_context: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Load a deck YAML file with all advanced features.

    Args:
        deck_path: Path to the deck YAML file
        include_tags: Tags to include for conditional filtering
        jinja_context: Additional context for Jinja2 templates

    Returns:
        Dictionary with config, data, and metadata
    """
    data = load_yaml_advanced(
        deck_path,
        jinja_context=jinja_context,
        include_tags=include_tags,
    )

    if not isinstance(data, dict):
        raise ValueError("Deck file must be a dictionary")

    return data
