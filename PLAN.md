# secscan-mcp — product plan

## Vision

**secscan-mcp** is a portable [Model Context Protocol](https://modelcontextprotocol.io) server that gives any AI coding assistant — in any IDE — a single, normalized API for security scanning.

One install. One report format. Works in Cursor, VS Code, Claude Desktop, Windsurf, and any other MCP host.

## What it does

| Category | Engines | MCP tool |
|----------|---------|----------|
| Secrets (working tree) | custom (built-in), gitleaks | `scan_secrets` |
| Secrets (git history) | git_history (built-in), gitleaks | `scan_secrets` + `include_git_history: true` |
| SAST | semgrep, bandit | `scan_code` |
| Dependencies | osv-scanner | `scan_dependencies` |
| IaC | checkov | `scan_iac` |
| All | whatever is installed | `scan_all` |

The **custom** engine scans current files with zero external tools. The **git_history** engine scans past commits for secrets that were removed from the working tree but remain in git history — critical because deleting a secret from code does not remove it from old commits.

Optional CLIs (gitleaks, semgrep, etc.) extend coverage when present; missing CLIs are skipped gracefully.

## Git history scanning

Many credential leaks happen in **commits**, not just the current checkout. Developers often delete a secret from source but forget it persists in git history — where it can be found by anyone with repo access or after a public push.

**How it works:**

1. Call `scan_secrets` with `"include_git_history": true`
2. **git_history** (built-in, requires `git`) walks recent commits (`git log -p`) and applies the same regex rules as the custom scanner to added lines in patches
3. **gitleaks** (optional) runs its own history-aware detect when installed
4. Findings include commit SHA, date, and remediation guidance (rotate + rewrite history)

**Limits:** `SECSCAN_GIT_MAX_COMMITS` (default `500`) caps how far back to scan.

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

### Phase 1 — Universal distribution ✅

Goal: any developer can install and configure in their IDE in under 2 minutes.

- [x] PLAN.md (this file)
- [x] README reframed as IDE-agnostic MCP server
- [x] Multi-IDE setup guide ([docs/setup.md](docs/setup.md))
- [x] Example MCP configs per host (`docs/examples/`)
- [x] Fix placeholder URLs in `pyproject.toml`
- [x] CI workflow (lint, typecheck, test on push)
- [x] Git history secret scanning (`git_history` engine)
- [x] Integration tests with `@pytest.mark.integration` marker

### Phase 2 — PyPI publish (current)

Goal: one-line install without cloning the repo.

- [ ] Publish `secscan-mcp` to PyPI (create GitHub Release `v0.1.0` — see [docs/PUBLISHING.md](docs/PUBLISHING.md))
- [x] Document `pip install secscan-mcp` and `uvx secscan-mcp`
- [x] GitHub Actions release workflow (tag → build → publish)
- [x] CHANGELOG.md and semver releases

### Phase 3 — MCP polish

Goal: agents use the tools correctly without hand-holding.

- [ ] Rich tool descriptions and parameter docs
- [ ] Server instructions for MCP hosts
- [ ] Expand `explain_finding` rule coverage
- [ ] Smoke-test in Cursor, VS Code, and Claude Desktop
- [ ] Default `include_git_history: true` guidance for pre-push / pre-PR workflows

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
| `SECSCAN_GIT_MAX_COMMITS` | `500` | Max commits to scan in git history mode |
