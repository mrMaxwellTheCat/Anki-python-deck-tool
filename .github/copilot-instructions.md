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
