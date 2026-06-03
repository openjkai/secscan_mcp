# secscan-mcp

MCP server that scans codebases for security issues: hardcoded secrets, SAST findings, vulnerable dependencies, and IaC misconfigurations. See [PLAN.md](PLAN.md) for the full design.

**Status:** Core MCP server implemented. Custom regex scanner works without external tools; install optional CLIs for broader coverage.

## Requirements

- Python 3.11+
- Optional external scanners (installed separately): `gitleaks`, `trufflehog`, `semgrep`, `bandit`, `osv-scanner`, `checkov`, etc.

## Quick start (development)

```bash
# Create venv and install dev tooling + pre-commit hooks
make install-dev
source .venv/bin/activate

# Lint, typecheck, test
make check

# Format on save: open in Cursor/VS Code (see .vscode/settings.json)
```

## Commands

| Command | Description |
|---------|-------------|
| `make install-dev` | Editable install + dev deps + `pre-commit install` |
| `make lint` | Ruff check |
| `make format` | Ruff format + auto-fix |
| `make typecheck` | Mypy (strict, `src/` only) |
| `make test` | Pytest |
| `make check` | lint + typecheck + test |
| `make pre-commit` | Run all pre-commit hooks on the repo |

## Project layout

```
src/secscan_mcp/     # Package source
tests/               # Unit and integration tests
.cursor/rules/       # Cursor agent rules (git, Python, project)
docs/                # Contributor docs
PLAN.md              # Implementation plan
```

## Optional scanner CLIs

| Tool | Category | Install (example) |
|------|----------|-------------------|
| gitleaks | secrets | `brew install gitleaks` |
| semgrep | SAST | `pip install semgrep` |
| bandit | SAST (Python) | `pip install bandit` |
| osv-scanner | dependencies | `brew install osv-scanner` |
| checkov | IaC | `pip install checkov` |

The **custom** engine always runs (built-in YAML rules).

## Cursor MCP config

Add to `~/.cursor/mcp.json`:

```json
{
  "mcpServers": {
    "secscan": {
      "command": "/Users/gohchenkai/Documents/mcp_test/.venv/bin/secscan-mcp"
    }
  }
}
```

Restart Cursor, then use tools like `scan_all` or `list_available_scanners`.

## Contributing

See [docs/CONTRIBUTING.md](docs/CONTRIBUTING.md).
