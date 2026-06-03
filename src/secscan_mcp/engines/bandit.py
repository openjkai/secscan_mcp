"""Bandit Python SAST adapter."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from secscan_mcp.engines._util import command_exists, parse_json, run_command
from secscan_mcp.normalize import Category, Finding, Severity, make_finding_id, map_severity


class BanditEngine:
    name = "bandit"
    category = Category.SAST

    def is_installed(self) -> bool:
        return command_exists("bandit")

    def run(self, root: Path, *, timeout: int) -> list[Finding]:
        cmd = ["bandit", "-r", str(root), "-f", "json", "-q"]
        proc = run_command(cmd, cwd=root, timeout=timeout)
        if proc.returncode not in (0, 1):
            msg = proc.stderr.strip() or f"bandit exited {proc.returncode}"
            raise RuntimeError(msg)
        return _parse_bandit(proc.stdout, root)


def _parse_bandit(stdout: str, root: Path) -> list[Finding]:
    data: Any = parse_json(stdout) if stdout.strip() else {}
    if not isinstance(data, dict):
        return []
    results = data.get("results", [])
    findings: list[Finding] = []
    for item in results:
        if not isinstance(item, dict):
            continue
        rule_id = str(item.get("test_id") or item.get("test_name") or "bandit")
        rel = _relative(str(item.get("filename") or ""), root)
        line = int(item.get("line_number") or 0)
        severity = map_severity(str(item.get("issue_severity")), default=Severity.MEDIUM)
        findings.append(
            Finding(
                id=make_finding_id(
                    engine="bandit",
                    rule_id=rule_id,
                    file=rel,
                    line=line,
                    category=Category.SAST,
                ),
                category=Category.SAST,
                severity=severity,
                title=str(item.get("issue_text") or rule_id),
                file=rel,
                line=line,
                rule_id=rule_id,
                engine="bandit",
                code_snippet=str(item.get("code") or ""),
                cwe=_bandit_cwe(item),
                remediation="See Bandit documentation for this test.",
                confidence=str(item.get("issue_confidence") or "medium").lower(),
            )
        )
    return findings


def _bandit_cwe(item: dict[str, Any]) -> str | None:
    issue_cwe = item.get("issue_cwe")
    if isinstance(issue_cwe, dict):
        cid = issue_cwe.get("id")
        return str(cid) if cid is not None else None
    return None


def _relative(file_path: str, root: Path) -> str:
    if not file_path:
        return ""
    path = Path(file_path)
    try:
        return str(path.resolve().relative_to(root.resolve()))
    except ValueError:
        return file_path
