# secscan-mcp

[![CI](https://github.com/openjkai/secscan_mcp/actions/workflows/ci.yml/badge.svg)](https://github.com/openjkai/secscan_mcp/actions/workflows/ci.yml)
[![PyPI](https://img.shields.io/pypi/v/secscan-mcp)](https://pypi.org/project/secscan-mcp/)

A portable **MCP server** for security scanning — works with **any AI coding assistant** that supports the [Model Context Protocol](https://modelcontextprotocol.io): Cursor, VS Code, Claude Desktop, Windsurf, Zed, Continue, and more.

Scan codebases for **hardcoded secrets**, **SAST issues**, **vulnerable dependencies**, and **IaC misconfigurations** — one install, one normalized report format.

The built-in **custom** scanner works with no extra tools. Install optional CLIs for broader coverage ([below](#optional-scanners)).

## Quick start

**1. Install** (Python 3.11+):

```bash
pip install secscan-mcp
```

Or run without installing (requires [uv](https://docs.astral.sh/uv/)):

```bash
uvx secscan-mcp
```

For MCP config with `uvx`, use `"command": "uvx"` and `"args": ["secscan-mcp"]` — see [setup guide](docs/setup.md).

<details>
<summary>Install from source</summary>

```bash
git clone https://github.com/openjkai/secscan_mcp.git
cd secscan_mcp && pip install .
```

</details>

**2. Add to your IDE** — pick your client:

| IDE / client | Config file | Guide |
|--------------|-------------|-------|
| Cursor | `~/.cursor/mcp.json` | [setup →](docs/setup.md#cursor) |
| VS Code | `.vscode/mcp.json` | [setup →](docs/setup.md#vs-code-github-copilot) |
| Claude Desktop | OS-specific (see guide) | [setup →](docs/setup.md#claude-desktop) |
| Claude Code | `~/.claude/settings.json` | [setup →](docs/setup.md#claude-code) |
| Windsurf | `~/.codeium/windsurf/mcp_config.json` | [setup →](docs/setup.md#windsurf) |
| Others | — | [Full setup guide](docs/setup.md) |

Minimal config (works in Cursor, Claude Desktop, Windsurf):

```json
{
  "mcpServers": {
    "secscan": {
      "command": "uvx",
      "args": ["secscan-mcp"]
    }
  }
}
```

If you installed with `pip install secscan-mcp`, you can use `"command": "secscan-mcp"` instead.

**3. Verify** — ask your agent: *"Call `list_available_scanners` and scan_secrets on this project."*

## MCP tools

| Tool | Purpose |
|------|---------|
| `list_available_scanners` | Which engines are installed on this machine |
| `scan_secrets` | Hardcoded credentials and secrets (optionally scan git commit history) |
| `scan_code` | SAST (semgrep, bandit) |
| `scan_dependencies` | Vulnerable packages (osv-scanner) |
| `scan_iac` | IaC misconfigurations (checkov) |
| `scan_all` | All available scanners, one unified report |
| `explain_finding` | Remediation hints for a `rule_id` |

Most scan tools accept `path` (directory to scan) and optional `severity_threshold` (`critical`, `high`, `medium`, `low`, `info`).

`scan_secrets` also accepts `include_git_history` (boolean). When `true`, scans past git commits for secrets removed from the working tree but still present in history — no extra tools required beyond `git`.

## Optional scanners

Install any of these to extend coverage. Missing CLIs are skipped — the server still runs.

| Engine | Category | Install (example) |
|--------|----------|-------------------|
| gitleaks | secrets | `brew install gitleaks` |
| semgrep | SAST | `pip install semgrep` |
| bandit | SAST (Python) | `pip install bandit` |
| osv-scanner | dependencies | `brew install osv-scanner` |
| checkov | IaC | `pip install checkov` |

After installing, run `list_available_scanners` again to confirm.

## Example prompts

- *"Call `list_available_scanners` and tell me what's installed."*
- *"Run `scan_secrets` with include_git_history on this repo — check if any secrets were ever committed."*
- *"Run `scan_all` with severity_threshold high and summarize the findings."*
- *"Explain the rule `internal-api-key`."*

## Configuration

Environment variables (optional):

| Variable | Default | Description |
|----------|---------|-------------|
| `SECSCAN_DEFAULT_TIMEOUT_SECONDS` | `300` | Per-engine scan timeout |
| `SECSCAN_MAX_FINDINGS` | `500` | Max findings per report |
| `SECSCAN_GIT_MAX_COMMITS` | `500` | Max commits scanned in git history mode |

Pass via MCP config `env` block — see [setup guide](docs/setup.md#environment-variables).

## Development

```bash
make install-dev   # editable install + dev tools
make check         # lint + typecheck + test
```

See [docs/CONTRIBUTING.md](docs/CONTRIBUTING.md) and [PLAN.md](PLAN.md).

## License

MIT
