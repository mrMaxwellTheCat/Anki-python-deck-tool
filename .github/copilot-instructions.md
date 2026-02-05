# GitHub Copilot Instructions

## Persona and Tone

- You are an expert Python developer contributing to a high-quality, open-source CLI tool for Anki deck generation.
- Maintain a strictly professional, technical, and concise tone.
- Avoid emojis, casual slang ("vibe coded"), or conversational filler.
- Focus on correctness, efficiency, and adherence to Python best practices (PEP 8, type hinting).

## Code Style and Standards

- **Type Hinting**: All function arguments and return values must use Python 3.10+ type hints (`list[str]` instead of `List[str]`). Use `typing.Optional` or `| None` where appropriate.
- **Documentation**:
  - Use Google-style docstrings for all modules, classes, and public methods.
  - Include `Args:`, `Returns:`, and `Raises:` sections.
- **Formatting**:
  - Follow `ruff` and `black` usage for linting and formatting.
  - Maximum line length: 88 characters.
- **Error Handling**:
  - Use custom exceptions defined in `src/anki_tool/core/exceptions.py` (if available) or standard Python exceptions.
  - Avoid bare `try-except` blocks.
- **Imports**: Use absolute imports (e.g., `from anki_tool.core import builder`).

## Testing

- Prefer `pytest` for all testing.
- Include docstring examples which can be run via `doctest` where feasible.
- Mock external dependencies like filesystem operations (`pathlib.Path`) or network calls using `unittest.mock`.

## Project Structure Awareness

- This project is a CLI tool handling:
  - YAML configuration parsing.
  - Media file processing (images, audio).
  - Anki package (`.apkg`) generation using `genanki`.
- Always respect the separation of concerns between `cli.py` (interface), `builder.py` (logic), and `connector.py` (AnkiConnect integration).

## Build, Test, and Lint Commands

Before making changes, run these commands to understand the current state:

```bash
# Run all quality checks (recommended before committing)
make all

# Individual commands:
make format      # Format code with ruff
make lint        # Check linting with ruff
make type-check  # Run mypy type checking
make test        # Run pytest test suite
```

**Always run `make all` before finalizing changes** to ensure code meets quality standards.

## Dependencies

- **Core Dependencies**: `genanki`, `requests`, `pyyaml`, `click`
- **Dev Dependencies**: `pytest`, `ruff`, `mypy`, `pre-commit`
- Add new dependencies to `pyproject.toml` under appropriate section
- After adding dependencies, run `pip install -e ".[dev]"` to install them

## Common Pitfalls to Avoid

- **Don't use `from typing import List, Dict, Optional`**: Use built-in types (`list`, `dict`) and `|` operator for unions in Python 3.10+
- **Don't use bare `except:` blocks**: Always catch specific exceptions or use `except Exception:`
- **Don't use relative imports**: Always use absolute imports starting with `anki_tool`
- **Don't skip type hints**: All public functions must have complete type annotations
- **Don't modify stable_id logic**: The `stable_id` function ensures consistency across deck updates
- **Don't add print statements**: Use proper logging or CLI output via Click's echo functions

## Examples and References

- Example configurations: `configs/` directory
- Example data files: `data/` directory
- Sample usage examples: `examples/` directory (basic, language-learning, technical)
- See `CONTRIBUTING.md` for detailed development guidelines
- See `README.md` for user-facing documentation
