# Agent guide (secscan-mcp)

## Project

Python MCP server wrapping security scanners (`gitleaks`, `semgrep`, `osv-scanner`, etc.). Full design: [PLAN.md](PLAN.md).

## Conventions

- Package: `src/secscan_mcp/`
- Run `make check` before finishing a change
- Use Ruff for format/lint; mypy strict on `src/`
- Minimize scope; one concern per commit when the user asks for commits

## Git

- **Do not commit** unless the user explicitly requests it
- Never commit secrets, `.env`, or `.scan-output/`
- Follow `.cursor/rules/git-commits.mdc` and `git-workflow.mdc`

## Current phase

**Phase 1 — Universal distribution.** Core engine is done (`normalize.py`, engine adapters, `runner.py`, MCP `server.py`). Focus now: multi-IDE docs ([docs/setup.md](docs/setup.md)), CI, integration tests, then PyPI publish (Phase 2). See [PLAN.md](PLAN.md).
