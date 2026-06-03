"""Normalized findings schema, redaction, deduplication, and summaries."""

from __future__ import annotations

import hashlib
import re
from dataclasses import asdict, dataclass, field
from enum import StrEnum
from typing import Any


class Severity(StrEnum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


class Category(StrEnum):
    SECRET = "secret"
    SAST = "sast"
    DEPENDENCY = "dependency"
    IAC = "iac"


_SEVERITY_ORDER: dict[Severity, int] = {
    Severity.CRITICAL: 0,
    Severity.HIGH: 1,
    Severity.MEDIUM: 2,
    Severity.LOW: 3,
    Severity.INFO: 4,
}

_ENGINE_SEVERITY_ALIASES: dict[str, Severity] = {
    "critical": Severity.CRITICAL,
    "error": Severity.HIGH,
    "high": Severity.HIGH,
    "warning": Severity.MEDIUM,
    "medium": Severity.MEDIUM,
    "moderate": Severity.MEDIUM,
    "low": Severity.LOW,
    "info": Severity.INFO,
    "informational": Severity.INFO,
    "note": Severity.INFO,
    "unknown": Severity.MEDIUM,
}


@dataclass(frozen=True)
class Finding:
    id: str
    category: Category
    severity: Severity
    title: str
    file: str
    line: int
    rule_id: str
    engine: str
    code_snippet: str = ""
    cwe: str | None = None
    cve: str | None = None
    remediation: str = ""
    confidence: str = "medium"

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["category"] = self.category.value
        data["severity"] = self.severity.value
        return data


@dataclass
class ScanSummary:
    total: int = 0
    by_severity: dict[str, int] = field(default_factory=dict)
    by_category: dict[str, int] = field(default_factory=dict)


@dataclass
class ScanReport:
    path: str
    findings: list[Finding]
    summary: ScanSummary
    engines_run: list[str] = field(default_factory=list)
    engines_skipped: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "path": self.path,
            "findings": [f.to_dict() for f in self.findings],
            "summary": {
                "total": self.summary.total,
                "by_severity": self.summary.by_severity,
                "by_category": self.summary.by_category,
            },
            "engines_run": self.engines_run,
            "engines_skipped": self.engines_skipped,
            "errors": self.errors,
        }


def map_severity(raw: str | None, *, default: Severity = Severity.MEDIUM) -> Severity:
    if not raw:
        return default
    key = raw.strip().lower()
    return _ENGINE_SEVERITY_ALIASES.get(key, default)


def severity_at_least(finding: Finding, threshold: Severity) -> bool:
    return _SEVERITY_ORDER[finding.severity] <= _SEVERITY_ORDER[threshold]


def filter_by_severity(findings: list[Finding], threshold: Severity | None) -> list[Finding]:
    if threshold is None:
        return findings
    return [f for f in findings if severity_at_least(f, threshold)]


def make_finding_id(
    *,
    engine: str,
    rule_id: str,
    file: str,
    line: int,
    category: Category,
) -> str:
    payload = f"{engine}:{category.value}:{rule_id}:{file}:{line}"
    return hashlib.sha256(payload.encode()).hexdigest()[:16]


def redact_secret(value: str, *, visible_prefix: int = 4) -> str:
    """Redact a secret value, keeping a short prefix and total length."""
    stripped = value.strip()
    if not stripped:
        return "[REDACTED]"
    if len(stripped) <= visible_prefix:
        return "*" * len(stripped)
    return f"{stripped[:visible_prefix]}…[{len(stripped)} chars]"


def redact_snippet(snippet: str) -> str:
    """Redact likely secret material inside a code snippet."""
    result = re.sub(
        r"(?i)((?:api[_-]?key|secret|password|token|auth)\s*[=:]\s*['\"]?)([^\s'\"]{4,})",
        lambda m: f"{m.group(1)}{redact_secret(m.group(2))}",
        snippet,
    )
    result = re.sub(r"(?i)Bearer\s+(\S+)", lambda m: f"Bearer {redact_secret(m.group(1))}", result)
    result = re.sub(r"AKIA[0-9A-Z]{16}", lambda m: redact_secret(m.group(0)), result)
    return re.sub(r"sk-[a-zA-Z0-9]{20,}", lambda m: redact_secret(m.group(0)), result)


def _dedupe_key(finding: Finding) -> tuple[str, str, int, str, str]:
    return (
        finding.category.value,
        finding.file,
        finding.line,
        finding.rule_id,
        finding.engine,
    )


def dedupe_findings(findings: list[Finding]) -> list[Finding]:
    """Merge duplicate findings from multiple engines."""
    seen: dict[tuple[str, str, int, str, str], Finding] = {}
    for finding in findings:
        key = _dedupe_key(finding)
        existing = seen.get(key)
        if existing is None:
            seen[key] = finding
            continue
        if _SEVERITY_ORDER[finding.severity] < _SEVERITY_ORDER[existing.severity]:
            seen[key] = finding
    return sorted(
        seen.values(),
        key=lambda f: (
            _SEVERITY_ORDER[f.severity],
            f.category.value,
            f.file,
            f.line,
        ),
    )


def build_summary(findings: list[Finding]) -> ScanSummary:
    by_severity: dict[str, int] = {s.value: 0 for s in Severity}
    by_category: dict[str, int] = {c.value: 0 for c in Category}
    for finding in findings:
        by_severity[finding.severity.value] += 1
        by_category[finding.category.value] += 1
    return ScanSummary(
        total=len(findings),
        by_severity=by_severity,
        by_category=by_category,
    )


def build_report(
    path: str,
    findings: list[Finding],
    *,
    engines_run: list[str] | None = None,
    engines_skipped: list[str] | None = None,
    errors: list[str] | None = None,
    severity_threshold: Severity | None = None,
    dedupe: bool = True,
) -> ScanReport:
    processed = dedupe_findings(findings) if dedupe else list(findings)
    processed = filter_by_severity(processed, severity_threshold)
    return ScanReport(
        path=path,
        findings=processed,
        summary=build_summary(processed),
        engines_run=engines_run or [],
        engines_skipped=engines_skipped or [],
        errors=errors or [],
    )
