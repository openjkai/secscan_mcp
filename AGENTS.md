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

**Phase 2 — PyPI publish.** Release workflow and docs ready; create GitHub Release `v0.1.0` to publish (see [docs/PUBLISHING.md](docs/PUBLISHING.md)). Next: MCP polish (Phase 3).
