"""Gitleaks secret scanner adapter."""

from __future__ import annotations

import tempfile
from pathlib import Path
from typing import Any

from secscan_mcp.engines._util import command_exists, parse_json, run_command
from secscan_mcp.normalize import (
    Category,
    Finding,
    Severity,
    make_finding_id,
    map_severity,
    redact_secret,
    redact_snippet,
)


class GitleaksEngine:
    name = "gitleaks"
    category = Category.SECRET

    def is_installed(self) -> bool:
        return command_exists("gitleaks")

    def run(self, root: Path, *, timeout: int, include_git_history: bool = False) -> list[Finding]:
        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as tmp:
            report_path = Path(tmp.name)

        cmd = [
            "gitleaks",
            "detect",
            "--source",
            str(root),
            "--report-format",
            "json",
            "--report-path",
            str(report_path),
        ]
        if not include_git_history:
            cmd.append("--no-git")

        proc = run_command(cmd, cwd=root, timeout=timeout)
        if proc.returncode not in (0, 1):  # 1 = leaks found
            msg = proc.stderr.strip() or proc.stdout.strip() or f"gitleaks exited {proc.returncode}"
            raise RuntimeError(msg)

        raw = report_path.read_text(encoding="utf-8") if report_path.exists() else "[]"
        report_path.unlink(missing_ok=True)
        return _parse_gitleaks(raw, root)


def _parse_gitleaks(raw: str, root: Path) -> list[Finding]:
    data: Any = parse_json(raw) if raw.strip() else []
    if isinstance(data, dict):
        items = data.get("findings") or data.get("results") or []
    elif isinstance(data, list):
        items = data
    else:
        items = []

    findings: list[Finding] = []
    for item in items:
        if not isinstance(item, dict):
            continue
        file_path = _relative_path(item.get("File") or item.get("file") or "", root)
        line = int(item.get("StartLine") or item.get("startLine") or item.get("line") or 0)
        rule_id = str(item.get("RuleID") or item.get("ruleID") or item.get("rule") or "gitleaks")
        secret = str(item.get("Secret") or item.get("secret") or "")
        snippet = redact_snippet(str(item.get("Match") or item.get("match") or secret))
        title = str(item.get("Description") or item.get("description") or rule_id)
        severity = map_severity(
            str(item.get("Severity") or item.get("severity")), default=Severity.HIGH
        )
        findings.append(
            Finding(
                id=make_finding_id(
                    engine="gitleaks",
                    rule_id=rule_id,
                    file=file_path,
                    line=line,
                    category=Category.SECRET,
                ),
                category=Category.SECRET,
                severity=severity,
                title=title,
                file=file_path,
                line=line,
                rule_id=rule_id,
                engine="gitleaks",
                code_snippet=snippet or redact_secret(secret),
                remediation="Remove the secret and rotate credentials; use environment variables or a secret manager.",
                confidence="high",
            )
        )
    return findings


def _relative_path(file_path: str, root: Path) -> str:
    if not file_path:
        return ""
    path = Path(file_path)
    try:
        return str(path.resolve().relative_to(root.resolve()))
    except ValueError:
        return file_path
