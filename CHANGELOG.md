# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Code coverage measurement with pytest-cov
- Comprehensive CLI tests with >90% coverage
- Codecov integration for coverage reporting
- Dependabot configuration for automated dependency updates
- Security scanning workflow with pip-audit and bandit
- CODE_OF_CONDUCT.md (Contributor Covenant)
- SECURITY.md for vulnerability disclosure
- Coverage badge in README

### Changed
- CI workflow now includes coverage reporting
- Updated README with coverage badge

### Infrastructure
- Added pytest-cov to dev dependencies
- Configured coverage thresholds (80% minimum)
- Added bandit configuration to pyproject.toml

## [0.1.0] - 2024-01-XX

### Added
- Initial release of Anki Python Deck Tool
- YAML-based deck building functionality
- AnkiConnect integration for pushing decks to Anki
- CLI with `build` and `push` commands
- Support for custom card templates and styling
- Tag support and ID-based tagging
- Stable deck and model ID generation
- Type hints throughout the codebase
- Comprehensive test suite for core modules
- CI/CD pipeline with GitHub Actions
  - Linting with ruff
  - Type checking with mypy
  - Multi-OS testing (Ubuntu, Windows, macOS)
  - Multi-Python version testing (3.10, 3.11, 3.12)
- Automated PyPI releases
- Pre-commit hooks configuration
- Examples directory with three use cases:
  - Basic flashcards
  - Language learning
  - Technical memorization
- Documentation:
  - Comprehensive README
  - CONTRIBUTING.md
  - ROADMAP.md
  - LICENSE (GPL-3.0)

### Technical Details
- Python 3.10+ required
- Uses genanki for Anki package generation
- Uses requests for AnkiConnect communication
- Uses Click for CLI framework
- Uses PyYAML for configuration parsing

[Unreleased]: https://github.com/mrMaxwellTheCat/Anki-python-deck-tool/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/mrMaxwellTheCat/Anki-python-deck-tool/releases/tag/v0.1.0
