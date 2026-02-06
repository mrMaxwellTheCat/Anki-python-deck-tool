# Makefile for Anki Python Deck Tool


.PHONY: help install test lint format type-check clean dev build build-exe install-system-wide all examples example-audio example-basic example-cloze example-historical example-language-learning example-math example-medical example-technical example-test

# Show this help message
help:  ## Show this help message
	@echo Available commands:                                                && \
	echo     install              - Install dependencies                     && \
	echo     dev                  - Install development dependencies         && \
	echo     test                 - Run tests                                && \
	echo     lint                 - Run linting checks                       && \
	echo     format               - Format code                              && \
	echo     type-check           - Run type checking                        && \
	echo     clean                - Clean build artifacts                    && \
	echo     build                - Build distribution packages              && \
	echo     build-exe            - Build single-file executable             && \
	echo     install-system-wide  - Install executable system-wide           && \
	echo     examples             - Build and push all example decks         && \
	echo     example-audio        - Build and push audio example             && \
	echo     example-basic        - Build and push basic example             && \
	echo     example-cloze        - Build and push cloze example             && \
	echo     example-historical   - Build and push historical example        && \
	echo     example-language-learning - Build and push language learning example && \
	echo     example-math         - Build and push math example              && \
	echo     example-medical      - Build and push medical example           && \
	echo     example-technical    - Build and push technical example         && \
	echo     example-test         - Build and push test example              && \
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

lint-fix:  ## Run linting checks with auto-fix
	python -m ruff check . --fix

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

all: format lint lint-fix type-check test  ## Run all checks

# Example deck targets

# Colors
CYAN := \033[36m
GREEN := \033[32m
YELLOW := \033[33m
RESET := \033[0m

## Helper function to build and push example decks
define build-push-example
	@echo "$(CYAN)🔨 Building $(1) example...$(RESET)"
	@python -m anki_yaml_tool.cli build --file examples/$(1)/deck.yaml --output examples/$(1)/deck.apkg
	@echo "$(YELLOW)📤 Pushing to Anki...$(RESET)"
	@python -m anki_yaml_tool.cli push --apkg examples/$(1)/deck.apkg
	@echo "$(GREEN)✅ Done!$(RESET)"
	@echo ""
endef

example-audio:  ## Build and push audio example
	$(call build-push-example,audio)

example-basic:  ## Build and push basic example
	$(call build-push-example,basic)

example-cloze:  ## Build and push cloze example
	$(call build-push-example,cloze)

example-historical: ## Build and push historical example
	$(call build-push-example,historical)

example-language-learning:  ## Build and push language learning example
	$(call build-push-example,language-learning)

example-math: ## Build and push math example
	$(call build-push-example,math)

example-medical: ## Build and push medical example
	$(call build-push-example,medical)

example-technical: ## Build and push technical example
	$(call build-push-example,technical)

example-test: ## Build and push test example
	$(call build-push-example,test)

examples: example-audio example-basic example-cloze example-historical example-language-learning example-math example-medical example-technical example-test  ## Build and push all example decks
