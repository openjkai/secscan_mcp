.PHONY: help install install-dev sync lint format typecheck test check pre-commit clean

PYTHON ?= python3
VENV ?= .venv
BIN = $(VENV)/bin

help:
	@echo "Targets:"
	@echo "  install      Create venv and install package"
	@echo "  install-dev  Install package + dev tools + pre-commit hooks"
	@echo "  sync         Reinstall editable package (dev extras)"
	@echo "  lint         Ruff linter"
	@echo "  format       Ruff formatter (write)"
	@echo "  typecheck    Mypy"
	@echo "  test         Pytest"
	@echo "  check        lint + typecheck + test"
	@echo "  pre-commit   Run all pre-commit hooks"
	@echo "  clean        Remove caches and build artifacts"

$(VENV)/bin/activate:
	$(PYTHON) -m venv $(VENV)
	$(BIN)/pip install -U pip

install: $(VENV)/bin/activate
	$(BIN)/pip install -e .

install-dev: $(VENV)/bin/activate
	$(BIN)/pip install -e ".[dev]"
	$(BIN)/pre-commit install
	@echo "Dev environment ready. Activate: source $(VENV)/bin/activate"

sync: $(VENV)/bin/activate
	$(BIN)/pip install -e ".[dev]"

lint:
	$(BIN)/ruff check src tests

format:
	$(BIN)/ruff format src tests
	$(BIN)/ruff check --fix src tests

typecheck:
	$(BIN)/mypy

test:
	$(BIN)/pytest

test-integration:
	$(BIN)/pytest -m integration

check: lint typecheck test

pre-commit:
	$(BIN)/pre-commit run --all-files

clean:
	rm -rf .venv .pytest_cache .mypy_cache .ruff_cache htmlcov .coverage
	rm -rf dist build *.egg-info src/*.egg-info
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
