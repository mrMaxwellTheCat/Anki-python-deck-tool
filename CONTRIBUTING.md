# Contributing to Anki Python Deck Tool

Thank you for your interest in contributing to the Anki Python Deck Tool! This document provides guidelines and instructions for contributing.

## Development Setup

### Prerequisites

- Python 3.10 or higher
- Git
- pip

### Setting Up Your Development Environment

1. **Clone the repository**:
   ```bash
   git clone https://github.com/mrMaxwellTheCat/Anki-python-deck-tool.git
   cd Anki-python-deck-tool
   ```

2. **Create a virtual environment**:
   ```bash
   python -m venv venv
   
   # On Windows:
   .\venv\Scripts\activate
   
   # On Linux/Mac:
   source venv/bin/activate
   ```

3. **Install dependencies**:
   ```bash
   # Install the package in editable mode with dev dependencies
   pip install -e ".[dev]"
   
   # Or use the Makefile
   make dev
   ```

4. **Set up pre-commit hooks** (optional but recommended):
   ```bash
   pre-commit install
   ```

## Development Workflow

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=anki_tool

# Run specific test file
pytest tests/test_builder.py

# Or use the Makefile
make test
```

### Code Formatting and Linting

We use `ruff` for both linting and formatting:

```bash
# Format code
ruff format .

# Check linting issues
ruff check .

# Fix linting issues automatically
ruff check --fix .

# Or use the Makefile
make format
make lint
```

### Type Checking

We use `mypy` for static type checking:

```bash
# Run type checking
mypy src

# Or use the Makefile
make type-check
```

### Running All Checks

To run all checks before committing:

```bash
make all
```

## Code Style Guidelines

### Python Style

- Follow PEP 8 style guidelines
- Use Python 3.10+ type hints (use `list[str]` instead of `List[str]`, and `X | Y` instead of `Optional[X]`)
- Maximum line length: 88 characters
- Use absolute imports (e.g., `from anki_tool.core import builder`)

### Documentation

- Use Google-style docstrings for all modules, classes, and public methods
- Include `Args:`, `Returns:`, and `Raises:` sections where applicable
- Example:

  ```python
  def build_deck(data_path: str, config_path: str) -> str:
      """Build an Anki deck from YAML files.
      
      Args:
          data_path: Path to the data YAML file.
          config_path: Path to the config YAML file.
      
      Returns:
          Path to the generated .apkg file.
      
      Raises:
          ConfigValidationError: If config file is invalid.
          DataValidationError: If data file is invalid.
      """
      pass
  ```

### Error Handling

- Use custom exceptions from `anki_tool.core.exceptions`
- Don't use bare `except:` blocks
- Always provide meaningful error messages

### Testing

- Write tests for all new features
- Aim for high code coverage
- Use descriptive test names that explain what is being tested
- Use `pytest` fixtures for common test setup

## Project Structure

```
anki-tool/
├── src/
│   └── anki_tool/
│       ├── __init__.py
│       ├── cli.py           # CLI entry points
│       └── core/
│           ├── __init__.py
│           ├── builder.py   # Deck building logic
│           ├── connector.py # AnkiConnect integration
│           └── exceptions.py # Custom exceptions
├── tests/
│   ├── __init__.py
│   ├── test_builder.py
│   ├── test_connector.py
│   └── test_exceptions.py
├── configs/                 # Example config files
├── data/                    # Example data files
├── .github/
│   └── workflows/           # CI/CD workflows
├── pyproject.toml
├── requirements.txt
└── README.md
```

## Submitting Changes

1. **Create a new branch** for your feature or bugfix:
   ```bash
   git checkout -b feature/my-new-feature
   ```

2. **Make your changes** following the code style guidelines.

3. **Run all checks** to ensure your code meets quality standards:
   ```bash
   make all
   ```

4. **Commit your changes** with a clear commit message:
   ```bash
   git commit -m "Add feature: description of the feature"
   ```

5. **Push to your fork**:
   ```bash
   git push origin feature/my-new-feature
   ```

6. **Create a Pull Request** on GitHub with:
   - A clear title and description
   - Reference to any related issues
   - Screenshots for UI changes (if applicable)

## Reporting Issues

When reporting issues, please include:

- A clear description of the problem
- Steps to reproduce the issue
- Expected behavior vs. actual behavior
- Your environment (OS, Python version, etc.)
- Relevant logs or error messages

## Feature Requests

We welcome feature requests! Please:

- Check if a similar request already exists
- Provide a clear use case
- Explain why this feature would be useful
- Consider contributing the feature yourself

## Questions?

If you have questions about contributing, feel free to:

- Open a discussion on GitHub
- Check existing issues and pull requests
- Review the [README.md](README.md) for more information

Thank you for contributing to the Anki Python Deck Tool!
