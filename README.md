# secscan-mcp

MCP server for Cursor that scans codebases for security issues: hardcoded secrets, SAST, vulnerable dependencies, and IaC misconfigurations.

The built-in **custom** scanner works with no extra tools. Install optional CLIs ([below](#optional-scanners)) for broader coverage.

## Install

Requires **Python 3.11+**.

```bash
git clone <repository-url>
cd mcp_test
python3 -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install .
```

Confirm the command exists:

```bash
which secscan-mcp
```

## Use in Cursor

### Option 1 — Any project (recommended)

Add to **`~/.cursor/mcp.json`** (create the file if needed):

```json
{
  "mcpServers": {
    "secscan": {
      "command": "/absolute/path/to/secscan-mcp"
    }
  }
}
```

Use the path from `which secscan-mcp` after install.

Then:

1. **Cmd+Shift+P** → **Developer: Reload Window**
2. **Cursor Settings → Tools & MCP** — `secscan` should show as connected (green)
3. Open the project you want to scan
4. In **Agent** chat, ask the agent to use the tools (see [examples](#example-prompts))

Works for any folder you open in Cursor, not only this repository.

### Option 2 — This repo only

If you develop or test **secscan-mcp** itself, use the included [`.cursor/mcp.json`](.cursor/mcp.json) and run `make install-dev` so `${workspaceFolder}/.venv/bin/secscan-mcp` exists.

## MCP tools

| Tool | Purpose |
|------|---------|
| `list_available_scanners` | Which engines are installed on this machine |
| `scan_secrets` | Hardcoded credentials and secrets |
| `scan_code` | SAST (semgrep, bandit) |
| `scan_dependencies` | Vulnerable packages (osv-scanner) |
| `scan_iac` | IaC misconfigurations (checkov) |
| `scan_all` | All available scanners, one report |
| `explain_finding` | Remediation hints for a `rule_id` |

Most tools accept `path` (directory to scan) and optional `severity_threshold` (`critical`, `high`, `medium`, `low`, `info`).

## Example prompts

- “Call `list_available_scanners` and tell me what’s installed.”
- “Run `scan_secrets` on this project.”
- “Run `scan_all` with severity_threshold high and summarize the findings.”
- “Explain the rule `internal-api-key`.”

## Optional scanners

| Tool | Category | Install (example) |
|------|----------|-------------------|
| gitleaks | secrets | `brew install gitleaks` |
| semgrep | SAST | `pip install semgrep` |
| bandit | SAST (Python) | `pip install bandit` |
| osv-scanner | dependencies | `brew install osv-scanner` |
| checkov | IaC | `pip install checkov` |

After installing, run `list_available_scanners` again to confirm.

## Troubleshooting

| Problem | What to try |
|---------|-------------|
| `secscan` missing in MCP list | Reload window; confirm `mcp.json` path and JSON syntax |
| Red / failed to start | Re-run `pip install .`; check `which secscan-mcp` matches config `command` |
| Agent doesn’t call tools | Use **Agent** mode; name the tool explicitly in your message |
| Only `custom` runs | Expected until optional CLIs are installed |

## Development

See [docs/CONTRIBUTING.md](docs/CONTRIBUTING.md) and [PLAN.md](PLAN.md).
