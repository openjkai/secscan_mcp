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

**Phase 3 — MCP polish.** v0.1.2 is on PyPI. Next ship: **v0.1.3** (server instructions, richer tool docs, `explain_finding` from rules YAML). Release via `make release-patch PYTHON=python3.11` — see [docs/PUBLISHING.md](docs/PUBLISHING.md).
