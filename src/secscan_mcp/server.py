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

app = Server("secscan-mcp")

_RULE_HELP: dict[str, str] = {
    "internal-api-key": "Remove hardcoded internal API keys; use env vars or a secret manager.",
    "hardcoded-jwt": "JWTs in source are exposed; use auth provider tokens with short TTL.",
    "generic-private-key-header": "Private keys in repos require rotation and removal from git history.",
}


@app.list_tools()
async def list_tools() -> list[Tool]:
    return [
        Tool(
            name="scan_secrets",
            description=(
                "Scan a directory for hardcoded secrets and credentials. "
                "Set include_git_history to also scan past git commits for secrets "
                "removed from the working tree (built-in git_history engine; gitleaks when installed)."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "Absolute or relative directory path",
                    },
                    "include_git_history": {
                        "type": "boolean",
                        "default": False,
                        "description": (
                            "Scan git commit history for secrets (not just current files). "
                            "Uses built-in git_history when git is available; also enables gitleaks history mode."
                        ),
                    },
                    "severity_threshold": {
                        "type": "string",
                        "enum": ["critical", "high", "medium", "low", "info"],
                        "description": "Minimum severity to include",
                    },
                },
                "required": ["path"],
            },
        ),
        Tool(
            name="scan_code",
            description="Run SAST scanners (semgrep, bandit) on a directory.",
            inputSchema={
                "type": "object",
                "properties": {
                    "path": {"type": "string"},
                    "severity_threshold": {
                        "type": "string",
                        "enum": ["critical", "high", "medium", "low", "info"],
                    },
                },
                "required": ["path"],
            },
        ),
        Tool(
            name="scan_dependencies",
            description="Scan lockfiles for vulnerable dependencies (osv-scanner).",
            inputSchema={
                "type": "object",
                "properties": {
                    "path": {"type": "string"},
                    "severity_threshold": {
                        "type": "string",
                        "enum": ["critical", "high", "medium", "low", "info"],
                    },
                },
                "required": ["path"],
            },
        ),
        Tool(
            name="scan_iac",
            description="Scan infrastructure-as-code for misconfigurations (checkov).",
            inputSchema={
                "type": "object",
                "properties": {
                    "path": {"type": "string"},
                    "severity_threshold": {
                        "type": "string",
                        "enum": ["critical", "high", "medium", "low", "info"],
                    },
                },
                "required": ["path"],
            },
        ),
        Tool(
            name="scan_all",
            description="Run all available scanners and return a unified report.",
            inputSchema={
                "type": "object",
                "properties": {
                    "path": {"type": "string"},
                    "severity_threshold": {
                        "type": "string",
                        "enum": ["critical", "high", "medium", "low", "info"],
                    },
                },
                "required": ["path"],
            },
        ),
        Tool(
            name="list_available_scanners",
            description="List scanners and whether each CLI is installed on this machine.",
            inputSchema={"type": "object", "properties": {}},
        ),
        Tool(
            name="explain_finding",
            description="Return remediation guidance for a rule_id.",
            inputSchema={
                "type": "object",
                "properties": {
                    "rule_id": {"type": "string"},
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
        text = _RULE_HELP.get(
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
