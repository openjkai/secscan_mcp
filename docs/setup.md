# MCP setup guide

Configure **secscan-mcp** in your IDE or AI client. The server uses **stdio** transport — the same config pattern works everywhere; only the config file location differs.

**Copy-paste examples:** [docs/examples/](examples/) (`uvx-mcp.json`, `cursor-mcp.json`, `vscode-mcp.json`, `claude-desktop-mcp.json`).

## Prerequisites

- **Python 3.11+**
- **secscan-mcp** installed (see [Install](#install))

Verify:

```bash
secscan-mcp --help 2>/dev/null || which secscan-mcp
```

If the command is not found, use the full path from `which secscan-mcp` in your config below.

## Install

### PyPI (recommended)

```bash
pip install secscan-mcp
```

### uvx (no install)

Requires [uv](https://docs.astral.sh/uv/). Ideal for MCP configs — always runs the latest compatible version:

```bash
uvx secscan-mcp
```

MCP config:

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

### From GitHub (no clone)

```bash
pip install git+https://github.com/openjkai/secscan_mcp.git
```

### From source (development)

```bash
git clone https://github.com/openjkai/secscan_mcp.git
cd secscan_mcp
python3 -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install .
```

---

## Config reference

**Recommended (uvx)** — no prior install, works on any machine with `uv`:

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

**After `pip install secscan-mcp`:**

```json
{
  "mcpServers": {
    "secscan": {
      "command": "secscan-mcp"
    }
  }
}
```

If `secscan-mcp` is not on your `PATH`, use the absolute path:

```json
{
  "mcpServers": {
    "secscan": {
      "command": "/full/path/to/secscan-mcp"
    }
  }
}
```

Or invoke via Python module:

```json
{
  "mcpServers": {
    "secscan": {
      "command": "python3",
      "args": ["-m", "secscan_mcp.server"]
    }
  }
}
```

**VS Code** uses a different root key — see [VS Code](#vs-code-github-copilot) below.

---

## Cursor

**Config file:** `~/.cursor/mcp.json` (global) or `.cursor/mcp.json` (project)

```json
{
  "mcpServers": {
    "secscan": {
      "command": "secscan-mcp"
    }
  }
}
```

**Steps:**

1. Save the config file.
2. **Cmd/Ctrl+Shift+P** → **Developer: Reload Window**
3. **Settings → Tools & MCP** — `secscan` should show connected (green)
4. In Agent chat, ask: *"Call list_available_scanners and scan_secrets on this project."*

---

## VS Code (GitHub Copilot)

**Config file:** `.vscode/mcp.json` (workspace) or user profile via **MCP: Open User Configuration**

VS Code uses `"servers"` (not `"mcpServers"`) and requires `"type": "stdio"`:

```json
{
  "servers": {
    "secscan": {
      "type": "stdio",
      "command": "secscan-mcp"
    }
  }
}
```

**Steps:**

1. Save `.vscode/mcp.json` in your project (or add to user config).
2. Reload the window or run **MCP: List Servers** from the Command Palette.
3. Enable the server if prompted.
4. In Copilot Chat (Agent mode), ask to run `scan_all` on the workspace.

**Tip:** VS Code can auto-discover MCP configs from Claude Desktop when `chat.mcp.discovery.enabled` is on.

---

## Claude Desktop

**Config file:**

| OS | Path |
|----|------|
| macOS | `~/Library/Application Support/Claude/claude_desktop_config.json` |
| Windows | `%APPDATA%\Claude\claude_desktop_config.json` |
| Linux | `~/.config/Claude/claude_desktop_config.json` |

```json
{
  "mcpServers": {
    "secscan": {
      "command": "secscan-mcp"
    }
  }
}
```

**Steps:**

1. Edit the config file (merge into existing `mcpServers` if you already have servers).
2. Restart Claude Desktop completely.
3. Look for the tools icon — `scan_secrets`, `scan_all`, etc. should appear.

---

## Claude Code

**Config file:** `~/.claude/settings.json` (user-level, top-level `mcpServers` field)

```json
{
  "mcpServers": {
    "secscan": {
      "command": "secscan-mcp"
    }
  }
}
```

Project-level override: `.mcp.json` at the project root (if your Claude Code version supports it).

---

## Windsurf

**Config file:** `~/.codeium/windsurf/mcp_config.json`

```json
{
  "mcpServers": {
    "secscan": {
      "command": "secscan-mcp"
    }
  }
}
```

Restart Windsurf after saving.

---

## Zed

**Config file:** `~/.config/zed/settings.json` — add under `"context_servers"`:

```json
{
  "context_servers": {
    "secscan": {
      "command": {
        "path": "secscan-mcp",
        "args": []
      }
    }
  }
}
```

Check [Zed MCP docs](https://zed.dev/docs/assistant/context-servers) for the latest format — it evolves quickly.

---

## Continue

**Config file:** `~/.continue/config.json` — add to `"experimental"` → `"modelContextProtocolServers"`:

```json
{
  "experimental": {
    "modelContextProtocolServers": [
      {
        "name": "secscan",
        "command": "secscan-mcp"
      }
    ]
  }
}
```

---

## Environment variables

Pass through the MCP config `env` block if needed:

```json
{
  "mcpServers": {
    "secscan": {
      "command": "secscan-mcp",
      "env": {
        "SECSCAN_DEFAULT_TIMEOUT_SECONDS": "600",
        "SECSCAN_MAX_FINDINGS": "1000"
      }
    }
  }
}
```

| Variable | Default | Description |
|----------|---------|-------------|
| `SECSCAN_DEFAULT_TIMEOUT_SECONDS` | `300` | Per-engine timeout (seconds) |
| `SECSCAN_MAX_FINDINGS` | `500` | Max findings per report |

---

## Verify it works

Ask your agent:

1. *"Call `list_available_scanners` and tell me what's installed."*
2. *"Run `scan_secrets` on this project and summarize findings."*

Expected: at minimum the **custom** secrets engine runs without any optional CLIs.

---

## Troubleshooting

| Problem | Fix |
|---------|-----|
| Server not listed | Reload/restart the IDE; check JSON syntax |
| Red / failed to start | Run `secscan-mcp` in a terminal — if it hangs, that's normal (stdio waits for input). Check `which secscan-mcp` matches config `command` |
| `command not found` | Use absolute path or `python3 -m secscan_mcp.server` with `args` |
| VS Code config ignored | Use `"servers"` root key, not `"mcpServers"`; add `"type": "stdio"` |
| Agent doesn't call tools | Name the tool explicitly; use Agent/Chat mode with tool access enabled |
| Only `custom` runs | Expected — install optional CLIs (see [README](../README.md#optional-scanners)) |

---

## Example prompts

- *"Call `list_available_scanners` and tell me what's installed."*
- *"Run `scan_secrets` on this project."*
- *"Run `scan_secrets` with include_git_history — check if secrets were ever committed."*
- *"Run `scan_all` with severity_threshold high and summarize the findings."*
- *"Explain the rule `internal-api-key`."*
