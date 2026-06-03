"""Tests for normalize module."""

from secscan_mcp.normalize import (
    Category,
    Finding,
    Severity,
    build_report,
    dedupe_findings,
    filter_by_severity,
    map_severity,
    redact_secret,
    redact_snippet,
)


def _finding(
    *,
    engine: str = "a",
    rule_id: str = "r1",
    file: str = "f.py",
    line: int = 1,
    severity: Severity = Severity.HIGH,
    category: Category = Category.SECRET,
) -> Finding:
    return Finding(
        id="abc",
        category=category,
        severity=severity,
        title="test",
        file=file,
        line=line,
        rule_id=rule_id,
        engine=engine,
    )


def test_map_severity_aliases() -> None:
    assert map_severity("ERROR") == Severity.HIGH
    assert map_severity("warning") == Severity.MEDIUM


def test_redact_secret() -> None:
    assert redact_secret("sk-abcdefghijklmnop") == "sk-a…[19 chars]"


def test_redact_snippet_masks_assignment() -> None:
    snippet = 'API_KEY = "supersecretvalue123"'
    redacted = redact_snippet(snippet)
    assert "supersecretvalue123" not in redacted


def test_dedupe_keeps_higher_severity() -> None:
    low = _finding(severity=Severity.LOW)
    high = _finding(severity=Severity.CRITICAL)
    result = dedupe_findings([low, high])
    assert len(result) == 1
    assert result[0].severity == Severity.CRITICAL


def test_filter_by_severity_threshold() -> None:
    findings = [_finding(severity=Severity.LOW), _finding(severity=Severity.CRITICAL)]
    filtered = filter_by_severity(findings, Severity.HIGH)
    assert len(filtered) == 1
    assert filtered[0].severity == Severity.CRITICAL


def test_build_report_summary() -> None:
    report = build_report("/tmp", [_finding(), _finding(file="other.py", line=2)])
    assert report.summary.total == 2
    assert report.summary.by_category["secret"] == 2
