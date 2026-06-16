.PHONY: help check-python install install-dev sync lint format typecheck test test-integration check build release release-patch release-minor release-major pre-commit clean

# Prefer Python 3.11+ (project requires >=3.11)
FIND_PYTHON := $(shell for c in python3.13 python3.12 python3.11; do \
	if $$c -c 'import sys; sys.exit(0 if sys.version_info >= (3, 11) else 1)' 2>/dev/null; then echo $$c; break; fi; done)
PYTHON ?= $(or $(FIND_PYTHON),python3)
VENV ?= .venv
BIN = $(VENV)/bin

check-python:
	@$(PYTHON) -c 'import sys; sys.exit(0 if sys.version_info >= (3, 11) else 1)' || \
	  (printf '\n✗ Python 3.11+ required (found: '; $(PYTHON) --version 2>&1; \
	   printf ')\n  Fix: sudo apt install python3.11 python3.11-venv\n        make install-dev PYTHON=python3.11\n\n'; \
	   exit 1)

help:
	@echo "Targets:"
	@echo "  install      Create venv and install package"
	@echo "  install-dev  Install package + dev tools + pre-commit hooks"
	@echo "  sync         Reinstall editable package (dev extras)"
	@echo "  lint         Ruff linter"
	@echo "  format       Ruff formatter (write)"
	@echo "  typecheck    Mypy"
	@echo "  test         Pytest"
	@echo "  test-integration  Pytest optional CLI tests"
	@echo "  build        Build sdist + wheel (dist/)"
	@echo "  release      Run scripts/release.sh (BUMP=patch|minor|major or VERSION=x.y.z)"
	@echo "  check        lint + typecheck + test"
	@echo "  pre-commit   Run all pre-commit hooks"
	@echo "  clean        Remove caches and build artifacts"

$(VENV)/bin/activate: check-python
	$(PYTHON) -m venv $(VENV)
	$(BIN)/pip install -U pip

install: $(VENV)/bin/activate
	$(BIN)/pip install -e .

install-dev: check-python $(VENV)/bin/activate
	$(BIN)/pip install -e ".[dev]"
	$(BIN)/pre-commit install
	@echo "Dev environment ready. Activate: source $(VENV)/bin/activate"

sync: check-python $(VENV)/bin/activate
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

build: $(VENV)/bin/activate
	$(BIN)/pip install -q build
	$(BIN)/python -m build

release:
	@test -n "$(VERSION)$(BUMP)" || (echo "Usage: make release BUMP=patch|minor|major  OR  make release VERSION=x.y.z" && exit 1)
	@PYTHON="$(PYTHON)" ./scripts/release.sh $(if $(DRY_RUN),--dry-run,) $(if $(YES),--yes,) $(or $(BUMP),$(VERSION))

release-patch:
	@$(MAKE) release BUMP=patch PYTHON="$(PYTHON)" $(if $(DRY_RUN),DRY_RUN=$(DRY_RUN),) $(if $(YES),YES=$(YES),)

release-minor:
	@$(MAKE) release BUMP=minor PYTHON="$(PYTHON)" $(if $(DRY_RUN),DRY_RUN=$(DRY_RUN),) $(if $(YES),YES=$(YES),)

release-major:
	@$(MAKE) release BUMP=major PYTHON="$(PYTHON)" $(if $(DRY_RUN),DRY_RUN=$(DRY_RUN),) $(if $(YES),YES=$(YES),)

check: lint typecheck test

pre-commit:
	$(BIN)/pre-commit run --all-files

clean:
	rm -rf .venv .pytest_cache .mypy_cache .ruff_cache htmlcov .coverage
	rm -rf dist build *.egg-info src/*.egg-info
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
