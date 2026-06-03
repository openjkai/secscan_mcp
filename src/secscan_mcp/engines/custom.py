"""Custom regex-based secret scanner (no external CLI)."""

from __future__ import annotations

import re
from importlib import resources
from pathlib import Path
from typing import Any

import yaml

from secscan_mcp.normalize import (
    Category,
    Finding,
    Severity,
    make_finding_id,
    map_severity,
    redact_snippet,
)

_RULES_PATH = "custom_secrets.yaml"


class CustomSecretsEngine:
    name = "custom"
    category = Category.SECRET

    def is_installed(self) -> bool:
        return True

    def run(self, root: Path, *, timeout: int) -> list[Finding]:
        del timeout  # unused; scan is in-process
        rules = _load_rules()
        findings: list[Finding] = []
        for file_path in _iter_text_files(root):
            try:
                content = file_path.read_text(encoding="utf-8", errors="ignore")
            except OSError:
                continue
            rel = str(file_path.relative_to(root))
            for rule in rules:
                pattern: re.Pattern[str] = rule["pattern"]
                for match in pattern.finditer(content):
                    line = content[: match.start()].count("\n") + 1
                    snippet = redact_snippet(match.group(0))
                    rule_id = str(rule["id"])
                    findings.append(
                        Finding(
                            id=make_finding_id(
                                engine="custom",
                                rule_id=rule_id,
                                file=rel,
                                line=line,
                                category=Category.SECRET,
                            ),
                            category=Category.SECRET,
                            severity=map_severity(
                                str(rule.get("severity", "high")),
                                default=Severity.HIGH,
                            ),
                            title=str(rule.get("title", rule_id)),
                            file=rel,
                            line=line,
                            rule_id=rule_id,
                            engine="custom",
                            code_snippet=snippet,
                            remediation=str(rule.get("remediation", "")),
                            confidence="medium",
                        )
                    )
        return findings


def _load_rules() -> list[dict[str, Any]]:
    rules_file = resources.files("secscan_mcp.rules").joinpath(_RULES_PATH)
    raw = yaml.safe_load(rules_file.read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        return []
    rules = raw.get("rules", [])
    loaded: list[dict[str, Any]] = []
    for rule in rules:
        if not isinstance(rule, dict) or "pattern" not in rule:
            continue
        entry = dict(rule)
        entry["pattern"] = re.compile(str(rule["pattern"]))
        loaded.append(entry)
    return loaded


_SKIP_DIRS = {
    ".git",
    ".venv",
    "venv",
    "node_modules",
    "__pycache__",
    ".ruff_cache",
    ".mypy_cache",
    "dist",
    "build",
}


def _iter_text_files(root: Path) -> list[Path]:
    files: list[Path] = []
    for path in root.rglob("*"):
        if not path.is_file():
            continue
        if any(part in _SKIP_DIRS for part in path.parts):
            continue
        if path.suffix.lower() in {".png", ".jpg", ".jpeg", ".gif", ".woff", ".woff2", ".ico"}:
            continue
        files.append(path)
    return files
