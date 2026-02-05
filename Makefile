# Makefile for Anki Python Deck Tool

.PHONY: help install test lint format type-check clean dev build all

help:  ## Show this help message
	@echo Available commands:
	@echo   install        Install dependencies
	@echo   dev            Install development dependencies
	@echo   test           Run tests
	@echo   lint           Run linting checks
	@echo   format         Format code
	@echo   type-check     Run type checking
	@echo   clean          Clean build artifacts
	@echo   build          Build distribution packages
	@echo   all            Run all checks

install:  ## Install dependencies
	pip install -e .

dev:  ## Install development dependencies
	pip install -e ".[dev]"
	pre-commit install

test:  ## Run tests
	pytest tests/ -v

lint:  ## Run linting checks
	ruff check .

format:  ## Format code
	ruff format .

type-check:  ## Run type checking
	mypy src --ignore-missing-imports

clean:  ## Clean build artifacts
	python -c "import shutil, pathlib; [shutil.rmtree(p, ignore_errors=True) for p in ['build', 'dist', *pathlib.Path('.').rglob('*.egg-info'), *pathlib.Path('.').rglob('__pycache__')]]; [p.unlink() for p in pathlib.Path('.').rglob('*.pyc')]"

build:  ## Build distribution packages
	python -m build

all: format lint type-check test  ## Run all checks
