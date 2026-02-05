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

all: format lint type-check test  ## Run all checks
