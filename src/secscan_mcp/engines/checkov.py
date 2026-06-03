"""Checkov IaC scanner adapter."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from secscan_mcp.engines._util import command_exists, parse_json, run_command
from secscan_mcp.normalize import Category, Finding, Severity, make_finding_id, map_severity


class CheckovEngine:
    name = "checkov"
    category = Category.IAC

    def is_installed(self) -> bool:
        return command_exists("checkov")

    def run(self, root: Path, *, timeout: int) -> list[Finding]:
        cmd = ["checkov", "-d", str(root), "--output", "json", "--quiet"]
        proc = run_command(cmd, cwd=root, timeout=timeout)
        if proc.returncode not in (0, 1):
            msg = proc.stderr.strip() or f"checkov exited {proc.returncode}"
            raise RuntimeError(msg)
        return _parse_checkov(proc.stdout, root)


def _parse_checkov(stdout: str, root: Path) -> list[Finding]:
    data: Any = parse_json(stdout) if stdout.strip() else []
    if isinstance(data, list) and data and isinstance(data[0], dict):
        payload = data[0]
    elif isinstance(data, dict):
        payload = data
    else:
        return []

    findings: list[Finding] = []
    for failed in payload.get("results", {}).get("failed_checks", []) or []:
        if not isinstance(failed, dict):
            continue
        rule_id = str(failed.get("check_id") or "checkov")
        rel = _relative(str(failed.get("file_path") or ""), root)
        line = int(failed.get("file_line_range", [0])[0]) if failed.get("file_line_range") else 0
        findings.append(
            Finding(
                id=make_finding_id(
                    engine="checkov",
                    rule_id=rule_id,
                    file=rel,
                    line=line,
                    category=Category.IAC,
                ),
                category=Category.IAC,
                severity=map_severity(str(failed.get("severity")), default=Severity.MEDIUM),
                title=str(failed.get("check_name") or rule_id),
                file=rel,
                line=line,
                rule_id=rule_id,
                engine="checkov",
                remediation=str(failed.get("guideline") or ""),
                confidence="medium",
            )
        )
    return findings


def _relative(file_path: str, root: Path) -> str:
    if not file_path:
        return ""
    path = Path(file_path)
    try:
        return str(path.resolve().relative_to(root.resolve()))
    except ValueError:
        return file_path
