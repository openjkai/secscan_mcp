# Changelog

All notable changes to this project are documented here. Version numbers follow [Semantic Versioning](https://semver.org/).

## [0.1.1] - 2026-06-16

### Added

- Git commit history secret scanning (`git_history` engine) via `include_git_history: true`
- PyPI publish workflow and release script (`make release-patch|minor|major`)
- Multi-IDE setup guide, example MCP configs, and `uvx` install path
- CI build job and package publishing docs

## [0.1.0] - 2026-06-16

First public release.

### Added

- MCP server with stdio transport for any IDE (Cursor, VS Code, Claude Desktop, Windsurf, etc.)
- Tools: `scan_secrets`, `scan_code`, `scan_dependencies`, `scan_iac`, `scan_all`, `list_available_scanners`, `explain_finding`
- Normalized finding schema with severity mapping, deduplication, and secret redaction
- Built-in **custom** secret scanner (no external CLI required)
- Built-in **git_history** scanner — detect secrets in past commits via `include_git_history: true`
- Optional engine adapters: gitleaks, semgrep, bandit, osv-scanner, checkov
- Multi-IDE setup guide and example MCP configs
- CI workflow (Python 3.11–3.13)

[0.1.1]: https://github.com/openjkai/secscan_mcp/releases/tag/v0.1.1
[0.1.0]: https://github.com/openjkai/secscan_mcp/releases/tag/v0.1.0
