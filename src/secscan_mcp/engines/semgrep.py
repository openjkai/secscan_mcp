"""Semgrep SAST adapter."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from secscan_mcp.engines._util import command_exists, parse_json, run_command
from secscan_mcp.normalize import Category, Finding, Severity, make_finding_id, map_severity


class SemgrepEngine:
    name = "semgrep"
    category = Category.SAST

    def is_installed(self) -> bool:
        return command_exists("semgrep")

    def run(self, root: Path, *, timeout: int) -> list[Finding]:
        cmd = [
            "semgrep",
            "scan",
            "--config",
            "p/security-audit",
            "--config",
            "p/secrets",
            "--json",
            "--quiet",
            str(root),
        ]
        proc = run_command(cmd, cwd=root, timeout=timeout)
        if proc.returncode not in (0, 1):
            msg = proc.stderr.strip() or f"semgrep exited {proc.returncode}"
            raise RuntimeError(msg)
        return _parse_semgrep(proc.stdout, root)


def _parse_semgrep(stdout: str, root: Path) -> list[Finding]:
    data: Any = parse_json(stdout) if stdout.strip() else {}
    if not isinstance(data, dict):
        return []
    results = data.get("results", [])
    findings: list[Finding] = []
    for item in results:
        if not isinstance(item, dict):
            continue
        check = item.get("check_id") or item.get("rule_id") or "semgrep"
        extra = item.get("extra") or {}
        if isinstance(extra, dict):
            metadata = extra.get("metadata")
            meta_severity = metadata.get("severity") if isinstance(metadata, dict) else None
            severity_raw = extra.get("severity") or meta_severity
            message = extra.get("message") or str(check)
        else:
            severity_raw = None
            message = str(check)
        path_item = item.get("path") or ""
        rel = _relative(path_item, root)
        start = item.get("start") or {}
        line = int(start.get("line", 0)) if isinstance(start, dict) else 0
        rule_id = str(check)
        findings.append(
            Finding(
                id=make_finding_id(
                    engine="semgrep",
                    rule_id=rule_id,
                    file=rel,
                    line=line,
                    category=Category.SAST,
                ),
                category=Category.SAST,
                severity=map_severity(
                    str(severity_raw) if severity_raw else None, default=Severity.MEDIUM
                ),
                title=str(message),
                file=rel,
                line=line,
                rule_id=rule_id,
                engine="semgrep",
                code_snippet=str(extra.get("lines", "")) if isinstance(extra, dict) else "",
                remediation="Review Semgrep rule guidance and fix the underlying issue.",
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
