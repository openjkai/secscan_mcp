# Changelog

All notable changes to this project are documented here. Version numbers follow [Semantic Versioning](https://semver.org/).

## [0.1.3] - 2026-06-22

### Fixed

- Update AGENTS.md and PLAN.md for Phase 3: polish MCP server with new features, including server instructions and richer tool documentation. Introduce rule remediation mapping in loader.py and add tests for rule loading functionality.
- Update README.md and setup.md: clarify Python 3.11+ requirement for installation, enhance installation instructions, and add PyPI badge for better visibility.


## [0.1.2] - 2026-06-16

### Fixed

- Update release process and documentation: enhance CHANGELOG.md auto-update functionality in the release script, ensuring it reflects the latest commits. Streamline release steps by clarifying prerequisites and improving user feedback during the release process.
- Enhance release workflow and documentation: add workflow_dispatch trigger to release.yml for manual execution, and expand PUBLISHING.md with detailed steps for setting up trusted publishing on PyPI, including environment creation and verification processes.


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

[0.1.2]: https://github.com/openjkai/secscan_mcp/releases/tag/v0.1.2

[0.1.3]: https://github.com/openjkai/secscan_mcp/releases/tag/v0.1.3
