# Contributing

## Setup

1. Clone the repo and `cd` into the project root.
2. Run `make install-dev` and activate `.venv`.
3. Open the folder in Cursor; install recommended extensions when prompted (Ruff, Python, EditorConfig).

## Before you commit

Run the full check suite:

```bash
make check
make pre-commit   # optional; same hooks run on git commit if installed
```

Pre-commit runs automatically on `git commit` after `make install-dev`.

## Code style

- **Formatter / linter:** [Ruff](https://docs.astral.sh/ruff/) (line length 100).
- **Types:** Mypy strict on `src/`.
- **Tests:** Pytest under `tests/`.
- Match existing patterns; keep changes focused.

## Git workflow

- Use feature branches off `main`.
- Do not commit `.env`, keys, or scan output with real secrets.
- Let the agent create commits only when you explicitly ask (see `.cursor/rules/git-commits.mdc`).

## Implementation order

Follow [PLAN.md](../PLAN.md) todos: normalize → engine adapters → runner → MCP tools → tests.
