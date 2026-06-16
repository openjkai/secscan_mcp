# Contributing

## Setup

1. Clone the repo and `cd` into the project root.
2. Run `make install-dev` and activate `.venv`.
3. Open the folder in your editor; install recommended extensions when prompted (Ruff, Python, EditorConfig).

## Commands

| Command | Description |
|---------|-------------|
| `make install-dev` | Editable install + dev deps + pre-commit hooks |
| `make check` | lint + typecheck + test |
| `make lint` | Ruff check |
| `make format` | Ruff format + auto-fix |
| `make typecheck` | Mypy |
| `make test` | Pytest (unit tests; integration skipped when CLIs missing) |
| `make test-integration` | Pytest with `-m integration` (requires optional CLIs) |
| `make build` | Build sdist + wheel to `dist/` |
| `make release VERSION=x.y.z` | Release script — tag, push, GitHub Release → PyPI |
| `make pre-commit` | Run all pre-commit hooks |

## Before you commit

```bash
make check
```

Pre-commit runs on `git commit` after `make install-dev`.

## Code style

- **Formatter / linter:** [Ruff](https://docs.astral.sh/ruff/) (line length 100)
- **Types:** Mypy strict on `src/`
- **Tests:** Pytest under `tests/`

## Git workflow

- Use feature branches off `main`.
- Do not commit `.env`, keys, or scan output with real secrets.
- See `.cursor/rules/git-commits.mdc` for agent commit rules.

## Implementation

Follow [PLAN.md](../PLAN.md).
