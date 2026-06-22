"""MCP server exposing security scan tools."""

from __future__ import annotations

import asyncio
import json
from typing import Any

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import TextContent, Tool

from secscan_mcp import __version__
from secscan_mcp.paths import PathValidationError
from secscan_mcp.rules.loader import rule_remediation_map
from secscan_mcp.runner import (
    list_scanners,
    parse_severity_threshold,
    report_to_json,
    scan,
    scan_code,
    scan_dependencies,
    scan_iac,
    scan_secrets,
)

app = Server(
    "secscan-mcp",
    version=__version__,
    instructions=(
        "Security scanning MCP server. Call list_available_scanners first to see what is "
        "installed. Use scan_secrets with include_git_history=true before pushing or opening "
        "a PR to catch secrets in git history — not just the working tree. Use scan_all for a "
        "full pass; explain_finding for remediation hints on a rule_id from any finding."
    ),
)

_SEVERITY_PROP = {
    "type": "string",
    "enum": ["critical", "high", "medium", "low", "info"],
    "description": "Minimum severity to include in results (default: info — all severities).",
}

_PATH_PROP = {
    "type": "string",
    "description": "Absolute or relative path to the project directory to scan.",
}


@app.list_tools()
async def list_tools() -> list[Tool]:
    return [
        Tool(
            name="scan_secrets",
            description=(
                "Detect hardcoded secrets and credentials in a directory. "
                "Runs the built-in custom scanner (no extra tools). "
                "When include_git_history is true, also scans past git commits for secrets "
                "removed from the working tree but still in history — recommended before push/PR. "
                "Uses git_history (built-in) and gitleaks (when installed)."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "path": _PATH_PROP,
                    "include_git_history": {
                        "type": "boolean",
                        "default": False,
                        "description": (
                            "Scan git commit history, not just current files. "
                            "Finds secrets deleted from source but still in old commits."
                        ),
                    },
                    "severity_threshold": _SEVERITY_PROP,
                },
                "required": ["path"],
            },
        ),
        Tool(
            name="scan_code",
            description=(
                "Static analysis (SAST) for code vulnerabilities and unsafe patterns. "
                "Uses semgrep and bandit when installed; skips missing engines."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "path": _PATH_PROP,
                    "severity_threshold": _SEVERITY_PROP,
                },
                "required": ["path"],
            },
        ),
        Tool(
            name="scan_dependencies",
            description=(
                "Scan lockfiles and manifests for known vulnerable dependencies (SCA). "
                "Uses osv-scanner when installed."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "path": _PATH_PROP,
                    "severity_threshold": _SEVERITY_PROP,
                },
                "required": ["path"],
            },
        ),
        Tool(
            name="scan_iac",
            description=(
                "Scan Terraform, CloudFormation, Kubernetes, and other IaC for "
                "misconfigurations. Uses checkov when installed."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "path": _PATH_PROP,
                    "severity_threshold": _SEVERITY_PROP,
                },
                "required": ["path"],
            },
        ),
        Tool(
            name="scan_all",
            description=(
                "Run every installed scanner (secrets, SAST, dependencies, IaC) and return "
                "one unified, deduplicated report. Does not enable git history unless you "
                "call scan_secrets separately with include_git_history."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "path": _PATH_PROP,
                    "severity_threshold": _SEVERITY_PROP,
                },
                "required": ["path"],
            },
        ),
        Tool(
            name="list_available_scanners",
            description=(
                "List all supported scanners and whether each engine CLI is installed. "
                "Call this before scanning to know which tools will run."
            ),
            inputSchema={"type": "object", "properties": {}},
        ),
        Tool(
            name="explain_finding",
            description=(
                "Return remediation guidance for a finding rule_id (from any scan result). "
                "Covers built-in secret rules; other engines fall back to generic advice."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "rule_id": {
                        "type": "string",
                        "description": "The rule_id field from a finding in a scan report.",
                    },
                },
                "required": ["rule_id"],
            },
        ),
    ]


def _handle_tool(name: str, arguments: dict[str, Any]) -> str:
    if name == "list_available_scanners":
        payload = [
            {"name": s.name, "category": s.category, "installed": s.installed}
            for s in list_scanners()
        ]
        return json.dumps({"scanners": payload, "version": __version__}, indent=2)

    if name == "explain_finding":
        rule_id = str(arguments.get("rule_id", ""))
        text = rule_remediation_map().get(
            rule_id,
            f"No built-in explanation for rule '{rule_id}'. Check the engine documentation for this rule.",
        )
        return json.dumps({"rule_id": rule_id, "remediation": text}, indent=2)

    path = str(arguments.get("path", ""))
    threshold = parse_severity_threshold(arguments.get("severity_threshold"))

    if name == "scan_secrets":
        report = scan_secrets(
            path,
            include_git_history=bool(arguments.get("include_git_history", False)),
            severity_threshold=threshold,
        )
    elif name == "scan_code":
        report = scan_code(path, severity_threshold=threshold)
    elif name == "scan_dependencies":
        report = scan_dependencies(path, severity_threshold=threshold)
    elif name == "scan_iac":
        report = scan_iac(path, severity_threshold=threshold)
    elif name == "scan_all":
        report = scan(path, severity_threshold=threshold)
    else:
        msg = f"Unknown tool: {name}"
        raise ValueError(msg)

    return report_to_json(report)


@app.call_tool()
async def call_tool(name: str, arguments: dict[str, Any]) -> list[TextContent]:
    try:
        payload = _handle_tool(name, arguments)
        return [TextContent(type="text", text=payload)]
    except PathValidationError as exc:
        return [TextContent(type="text", text=json.dumps({"error": str(exc)}, indent=2))]
    except ValueError as exc:
        return [TextContent(type="text", text=json.dumps({"error": str(exc)}, indent=2))]


async def _run_server() -> None:
    async with stdio_server() as (read_stream, write_stream):
        await app.run(read_stream, write_stream, app.create_initialization_options())


def main() -> None:
    asyncio.run(_run_server())
