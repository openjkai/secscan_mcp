"""OSV-Scanner dependency vulnerability adapter."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from secscan_mcp.engines._util import command_exists, parse_json, run_command
from secscan_mcp.normalize import Category, Finding, Severity, make_finding_id, map_severity


class OsvEngine:
    name = "osv-scanner"
    category = Category.DEPENDENCY

    def is_installed(self) -> bool:
        return command_exists("osv-scanner")

    def run(self, root: Path, *, timeout: int) -> list[Finding]:
        cmd = ["osv-scanner", "--recursive", str(root), "--format", "json"]
        proc = run_command(cmd, cwd=root, timeout=timeout)
        if proc.returncode not in (0, 1):
            msg = proc.stderr.strip() or f"osv-scanner exited {proc.returncode}"
            raise RuntimeError(msg)
        return _parse_osv(proc.stdout, root)


def _parse_osv(stdout: str, root: Path) -> list[Finding]:
    del root
    data: Any = parse_json(stdout) if stdout.strip() else {}
    if not isinstance(data, dict):
        return []
    results = data.get("results", [])
    findings: list[Finding] = []
    for project in results:
        if not isinstance(project, dict):
            continue
        source = project.get("source", {})
        manifest = ""
        if isinstance(source, dict):
            manifest = str(source.get("path") or "")
        for vuln in project.get("vulnerabilities", []) or []:
            if not isinstance(vuln, dict):
                continue
            pkg = vuln.get("package", {}) or {}
            name = str(pkg.get("name") or "unknown") if isinstance(pkg, dict) else "unknown"
            vid = str(vuln.get("id") or "OSV")
            severity = _osv_severity(vuln)
            findings.append(
                Finding(
                    id=make_finding_id(
                        engine="osv-scanner",
                        rule_id=vid,
                        file=manifest or name,
                        line=0,
                        category=Category.DEPENDENCY,
                    ),
                    category=Category.DEPENDENCY,
                    severity=severity,
                    title=f"Vulnerable dependency: {name}",
                    file=manifest,
                    line=0,
                    rule_id=vid,
                    engine="osv-scanner",
                    cve=vid if vid.startswith("CVE-") else None,
                    remediation="Upgrade to a patched version per the OSV advisory.",
                    confidence="high",
                )
            )
    return findings


def _osv_severity(vuln: dict[str, Any]) -> Severity:
    for item in vuln.get("severity", []) or []:
        if isinstance(item, dict):
            return map_severity(str(item.get("type") or item.get("score")), default=Severity.HIGH)
    return Severity.HIGH
