# AI Assistant Instructions

This file provides instructions for GitHub Copilot, Claude, and other AI coding assistants working on this project.

## Persona and Tone

- You are an expert Python developer contributing to a high-quality, open-source CLI tool for Anki deck generation.
- Maintain a strictly professional, technical, and concise tone.
- Avoid emojis, casual slang ("vibe coded"), or conversational filler.
- Focus on correctness, efficiency, and adherence to Python best practices (PEP 8, type hinting).

## Code Style and Standards

### Type Hinting

- All function arguments and return values must use Python 3.10+ type hints (`list[str]` instead of `List[str]`)
- Use `| None` for optional types instead of `Optional[T]`
- Use `typing.Optional` or `| None` where appropriate
- All public functions must have complete type annotations

### Documentation

- Use Google-style docstrings for all modules, classes, and public methods
- Include `Args:`, `Returns:`, and `Raises:` sections
- Keep docstrings concise but complete
- Add inline comments only for complex or non-obvious logic

### Formatting

- Follow `ruff` for linting and formatting (replaces black)
- Maximum line length: 88 characters
- Use `ruff format` to auto-format code
- Use `ruff check --fix` to auto-fix linting issues

### Error Handling

- Use custom exceptions defined in `src/anki_yaml_tool/core/exceptions.py`:
  - `ConfigValidationError` - Invalid configuration file
  - `DataValidationError` - Invalid data file
  - `MediaMissingError` - Missing media file
  - `AnkiConnectError` - AnkiConnect communication failure
  - `DeckBuildError` - General deck building error
- Avoid bare `try-except` blocks - always catch specific exceptions
- Include context in error messages (file paths, actions that failed)

### Imports

- Use absolute imports (e.g., `from anki_yaml_tool.core import builder`)
- Never use relative imports
- Group imports: stdlib → third-party → local
- Use `from typing import` only when necessary (prefer built-in types)

## Testing

### Test Requirements

- Prefer `pytest` for all testing
- Maintain minimum 80% code coverage
- Write tests for all new features and bug fixes
- Use descriptive test names: `test_<feature>_<scenario>_<expected_result>`

### Testing Practices

- Mock external dependencies using `unittest.mock`:
  - Filesystem operations (`pathlib.Path`)
  - Network calls (AnkiConnect, HTTP requests)
  - External command execution
- Use fixtures for common test setup
- Include both positive and negative test cases
- Test error handling and edge cases

### Running Tests

```bash
# Quick test
pytest tests/

# With coverage
pytest tests/ --cov=anki_yaml_tool --cov-report=term-missing
```

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

## Project Structure Awareness

### Architecture

This project is a CLI tool with clean separation of concerns:

- **`cli.py`**: Command-line interface (Click commands)
- **`builder.py`**: Deck building logic (genanki integration)
- **`connector.py`**: AnkiConnect integration (HTTP API)
- **`exceptions.py`**: Custom exception classes

### Key Components

- **YAML configuration parsing**: Note type definitions (fields, templates, CSS)
- **Media file processing**: Images, audio (future: auto-detection)
- **Anki package generation**: Using `genanki` library
- **AnkiConnect integration**: Push decks directly to Anki Desktop

### Important Functions

- **`stable_id(name)`**: Generates deterministic IDs for decks/models
  - **DO NOT modify** - ensures consistency across deck updates
  - Uses SHA256 hash of name converted to integer
- **`add_note()`**: Adds notes to deck with field mapping
- **`import_package()`**: Uploads .apkg files via AnkiConnect

## Dependencies

### Core Dependencies

- `genanki` - Anki package generation
- `requests` - HTTP requests for AnkiConnect
- `pyyaml` - YAML parsing
- `click` - CLI framework

See `pyproject.toml` for specific version requirements.

### Dev Dependencies

- `pytest` - Testing framework
- `pytest-cov` - Coverage reporting
- `ruff` - Linting and formatting
- `mypy` - Static type checking
- `pre-commit` - Git hooks
- `pip-audit` - Security vulnerability scanning
- `bandit[toml]` - Security linting

See `pyproject.toml` for specific version requirements.

### Adding Dependencies

1. Add to `pyproject.toml` under appropriate section (`dependencies` or `optional-dependencies`)
2. Run `pip install -e ".[dev]"` to install
3. Document the dependency if it introduces new functionality or requirements

## Common Pitfalls to Avoid

### Type Hints (Python 3.10+)

❌ **Don't**: `from typing import List, Dict, Optional`
✅ **Do**: Use built-in types (`list`, `dict`) and `|` operator

```python
# Bad
from typing import List, Optional
def foo(items: List[str]) -> Optional[int]:

# Good
def foo(items: list[str]) -> int | None:
```

### Exception Handling

❌ **Don't**: Bare `except:` blocks or catching `Exception` without re-raising
✅ **Do**: Catch specific exceptions

```python
# Bad
try:
    build_deck()
except:
    pass

# Good
try:
    build_deck()
except ConfigValidationError as e:
    click.echo(f"Error: {e}", err=True)
    sys.exit(1)
```

### Imports

❌ **Don't**: Relative imports or importing from `typing` unnecessarily
✅ **Do**: Absolute imports, built-in types

```python
# Bad
from .builder import AnkiBuilder
from typing import List, Dict

# Good
from anki_yaml_tool.core.builder import AnkiBuilder
```

### Printing Output

❌ **Don't**: Use `print()` statements
✅ **Do**: Use Click's `echo()` or proper logging

```python
# Bad
print("Building deck...")

# Good
click.echo("Building deck...")
```

### Modifying Core Logic

❌ **Don't**: Modify `stable_id()` function
✅ **Do**: Use it as-is to ensure deck consistency

The `stable_id` function ensures decks/models have the same ID across updates, preserving user progress.

## File Organization

### Creating Summary/Documentation Files

**IMPORTANT**: Do NOT create summary, setup, or implementation files in the root directory.

**✅ Correct locations**:

- Technical documentation → `docs/` directory
- Implementation summaries → `docs/` directory
- Setup guides → `docs/` directory
- VSCode-related docs → `.vscode/README.md` or `docs/`

**❌ Avoid creating in root**:

- `IMPLEMENTATION_SUMMARY.md`
- `SETUP_GUIDE.md`
- `*_SUMMARY.md`
- `*_SETUP.md`

**Root directory is reserved for**:

- `README.md` - Main project documentation
- `CONTRIBUTING.md` - Contribution guidelines
- `CHANGELOG.md` - Version history
- `CODE_OF_CONDUCT.md` - Community standards
- `SECURITY.md` - Security policy
- `ROADMAP.md` - Project roadmap
- `LICENSE` - License file

### Documentation Structure

```
docs/
├── [technical documentation files]
├── [implementation notes]
└── [setup guides]

.vscode/
├── tasks.json                  # Task definitions
└── README.md                   # VSCode setup guide (optional)

.github/
├── copilot-instructions.md     # This file (AI instructions)
├── workflows/                  # GitHub Actions
└── ISSUE_TEMPLATE/            # Issue templates
```

## Examples and References

### Example Files

- **Configurations**: See `examples/` directory for configuration file examples
- **Data files**: See `examples/` directory for data file examples

### Documentation

- **User docs**: `README.md` - Installation, usage, examples
- **Contributor docs**: `CONTRIBUTING.md` - Development setup, workflow
- **Project plans**: `ROADMAP.md` - Future features and phases
- **Security**: `SECURITY.md` - Vulnerability reporting
- **Community**: `CODE_OF_CONDUCT.md` - Conduct standards
- **Changes**: `CHANGELOG.md` - Version history
- **Technical docs**: `docs/` - Implementation details, setup guides

### CI/CD and Quality

- **Workflows**: `.github/workflows/` - GitHub Actions for CI, security scanning, and releases
- **Pre-commit**: `.pre-commit-config.yaml` - Git hooks for code quality

## Git Workflow

### Committing Changes

- Write clear, descriptive commit messages
- Use conventional commit format when appropriate:
  - `feat:` - New feature
  - `fix:` - Bug fix
  - `docs:` - Documentation changes
  - `test:` - Test changes
  - `refactor:` - Code refactoring
  - `chore:` - Maintenance tasks

### Before Committing

1. Run `make all` for full CI checks
2. Ensure all tests pass
3. Verify coverage remains above 80%
4. Check no linting errors
5. Verify type checking passes

### Creating Pull Requests

- Fill out the PR template completely
- Ensure CI passes on all platforms
- Update `CHANGELOG.md` in "Unreleased" section
- Add/update tests for changes
- Update documentation if needed

## Code Review Guidelines

When reviewing (or having code reviewed):

- Check test coverage for new code
- Verify type hints are complete
- Ensure docstrings follow Google style
- Confirm error handling is appropriate
- Validate no security issues (bandit, pip-audit)
- Check adherence to project patterns

## Security Considerations

### Input Validation

- Always validate YAML input (config and data files)
- Check file paths exist before reading
- Sanitize user input before displaying
- Use `yaml.safe_load()`, never `yaml.load()`

### Dependencies

- Security scans run weekly via GitHub Actions
- Review Dependabot PRs promptly
- Check for known vulnerabilities with `pip-audit`
- Keep dependencies up to date

### AnkiConnect

- AnkiConnect runs on `127.0.0.1:8765` (localhost only)
- Never expose AnkiConnect to the internet
- Assume AnkiConnect is running locally and trusted

## Performance Considerations

- Deck building should be fast (< 1 second for 100 cards)
- Minimize file I/O operations
- Cache parsed YAML where appropriate
- Use generators for large datasets
- Profile before optimizing

## Compatibility

- **Python**: 3.10+ required (use modern type hints)
- **Platforms**: Windows, macOS, Linux (test on all three)
- **Anki**: Desktop version with AnkiConnect add-on
- **Dependencies**: Keep minimum versions in sync with CI

## Quick Reference

| Task           | Command                             |
| -------------- | ----------------------------------- |
| Run all checks | `make all`                          |
| Format code    | `ruff format .`                     |
| Fix linting    | `ruff check --fix .`                |
| Type check     | `mypy src --ignore-missing-imports` |
| Run tests      | `pytest tests/`                     |
| Coverage       | `pytest --cov=anki_yaml_tool`       |
| Security scan  | `pip-audit && bandit -r src/`       |
| Install deps   | `pip install -e ".[dev]"`           |

## Getting Help

- **Issues**: Use `.github/ISSUE_TEMPLATE/` templates
- **PRs**: Use `.github/PULL_REQUEST_TEMPLATE.md`
- **Community**: Follow `CODE_OF_CONDUCT.md`
- **Security**: Report via `SECURITY.md` process
