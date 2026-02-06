# Makefile for Anki Python Deck Tool


.PHONY: help install test lint format type-check clean dev build build-exe install-system-wide all examples example-basic example-language example-technical example-math

# Show this help message
help:  ## Show this help message
	@echo Available commands: && \
	echo     install              - Install dependencies && \
	echo     dev                  - Install development dependencies && \
	echo     test                 - Run tests && \
	echo     lint                 - Run linting checks && \
	echo     format               - Format code && \
	echo     type-check           - Run type checking && \
	echo     clean                - Clean build artifacts && \
	echo     build                - Build distribution packages && \
	echo     build-exe            - Build single-file executable && \
	echo     install-system-wide  - Install executable system-wide && \
	echo     examples             - Build and push all example decks && \
	echo     example-basic        - Build and push basic example && \
	echo     example-language     - Build and push language learning example && \
	echo     example-technical    - Build and push technical example && \
	echo     example-math         - Build and push math example && \
	echo     all                  - Run all checks


install:  ## Install dependencies
	python -m pip install -e .

dev:  ## Install development dependencies
	python -m pip install -e ".[dev]"
	python -m pre_commit install

test:  ## Run tests
	python -m pytest tests/ -v

lint:  ## Run linting checks
	python -m ruff check .

format:  ## Format code
	python -m ruff format .

type-check:  ## Run type checking
	python -m mypy src --ignore-missing-imports

clean:  ## Clean build artifacts
	python -c "import shutil, pathlib; [shutil.rmtree(p, ignore_errors=True) for p in ['build', 'dist', *pathlib.Path('.').rglob('*.egg-info'), *pathlib.Path('.').rglob('__pycache__')]]; [p.unlink() for p in pathlib.Path('.').rglob('*.pyc')]"

build:  ## Build distribution packages
	python -m build

build-exe:  ## Build single-file executable
	python scripts/build.py

install-system-wide:  ## Install executable system-wide
ifeq ($(OS),Windows_NT)
	powershell -ExecutionPolicy Bypass -File scripts/install-system-wide.ps1
else
	bash scripts/install-system-wide.sh
endif

all: format lint type-check test  ## Run all checks

# Example deck targets
example-basic:  ## Build and push basic example
	python -m anki_yaml_tool.cli build --data examples/basic/data.yaml --config examples/basic/config.yaml --output examples/basic/deck.apkg --deck-name "Testing::Basic Example"
	python -m anki_yaml_tool.cli push --apkg examples/basic/deck.apkg

example-language:  ## Build and push language learning example
	python -m anki_yaml_tool.cli build --data examples/language-learning/data.yaml --config examples/language-learning/config.yaml --output examples/language-learning/deck.apkg --deck-name "Testing::Language Learning"
	python -m anki_yaml_tool.cli push --apkg examples/language-learning/deck.apkg

example-technical:  ## Build and push technical example
	python -m anki_yaml_tool.cli build --data examples/technical/data.yaml --config examples/technical/config.yaml --output examples/technical/deck.apkg --deck-name "Testing::Technical Example"
	python -m anki_yaml_tool.cli push --apkg examples/technical/deck.apkg

example-math: ## Build and push math example
	python -m anki_yaml_tool.cli build --data examples/math/data.yaml --config examples/math/config.yaml --output examples/math/deck.apkg --deck-name "Testing::Math Example"
	python -m anki_yaml_tool.cli push --apkg examples/math/deck.apkg

example-audio: ## Build and push audio example
	python -m anki_yaml_tool.cli build --data examples/audio/data.yaml --config examples/audio/config.yaml --output examples/audio/deck.apkg --deck-name "Testing::Audio Example"
	python -m anki_yaml_tool.cli push --apkg examples/audio/deck.apkg

examples: example-basic example-language example-technical example-math example-audio ## Build and push all example decks
