# secscan-mcp — product plan

## Vision

**secscan-mcp** is a portable [Model Context Protocol](https://modelcontextprotocol.io) server that gives any AI coding assistant — in any IDE — a single, normalized API for security scanning.

One install. One report format. Works in Cursor, VS Code, Claude Desktop, Windsurf, and any other MCP host.

## What it does

| Category | Engines | MCP tool |
|----------|---------|----------|
| Secrets | custom (built-in), gitleaks | `scan_secrets` |
| SAST | semgrep, bandit | `scan_code` |
| Dependencies | osv-scanner | `scan_dependencies` |
| IaC | checkov | `scan_iac` |
| All | whatever is installed | `scan_all` |

The **custom** engine runs with zero external tools. Optional CLIs extend coverage when present; missing CLIs are skipped gracefully.

## Architecture

```
MCP host (any IDE)
    │  stdio
    ▼
server.py          ← MCP tools
    │
runner.py          ← parallel runs, timeouts, path safety
    │
engines/*          ← one adapter per scanner CLI
    │
normalize.py       ← Finding schema, severity, dedupe, redaction
```

## Phases

### Phase 0 — Core engine ✅

- [x] Normalized `Finding` / `ScanReport` schema
- [x] Engine adapters (custom, gitleaks, semgrep, bandit, osv, checkov)
- [x] Parallel runner with timeouts and path validation
- [x] MCP server with 7 tools (stdio transport)
- [x] Unit tests for normalize, paths, runner, custom engine

### Phase 1 — Universal distribution (current)

Goal: any developer can install and configure in their IDE in under 2 minutes.

- [x] PLAN.md (this file)
- [x] README reframed as IDE-agnostic MCP server
- [x] Multi-IDE setup guide ([docs/setup.md](docs/setup.md))
- [x] Example MCP configs per host (`docs/examples/`)
- [x] Fix placeholder URLs in `pyproject.toml`
- [x] CI workflow (lint, typecheck, test on push)
- [ ] Integration tests with `@pytest.mark.integration` marker

### Phase 2 — PyPI publish

Goal: one-line install without cloning the repo.

- [ ] Publish `secscan-mcp` to PyPI
- [ ] Document `pip install secscan-mcp` and `uvx secscan-mcp`
- [ ] GitHub Actions release workflow (tag → build → publish)
- [ ] CHANGELOG.md and semver releases

### Phase 3 — MCP polish

Goal: agents use the tools correctly without hand-holding.

- [ ] Rich tool descriptions and parameter docs
- [ ] Server instructions for MCP hosts
- [ ] Expand `explain_finding` rule coverage
- [ ] Smoke-test in Cursor, VS Code, and Claude Desktop

### Phase 4 — Community & discovery

Goal: become the default security MCP.

- [ ] SECURITY.md, issue templates
- [ ] Submit to MCP registries and awesome lists
- [ ] Optional VS Code manifest for "Install from manifest"
- [ ] Optional Docker image for team deployments

## Non-goals (for now)

- HTTP/SSE transport (stdio covers all major hosts today)
- IDE-specific plugins or extensions
- Hosted/remote scan service

## Quality gate

Before marking any phase done:

```bash
make check   # ruff + mypy + pytest
```

Integration tests (when CLIs are installed):

```bash
pytest -m integration
```

## Environment variables

| Variable | Default | Description |
|----------|---------|-------------|
| `SECSCAN_DEFAULT_TIMEOUT_SECONDS` | `300` | Per-engine scan timeout |
| `SECSCAN_MAX_FINDINGS` | `500` | Cap findings in a single report |
