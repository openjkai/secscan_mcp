"""Scan orchestration: parallel engine runs, timeouts, reporting."""

from __future__ import annotations

import json
import os
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from pathlib import Path

from secscan_mcp.engines import ALL_ENGINES, ENGINES_BY_CATEGORY
from secscan_mcp.engines.base import Engine
from secscan_mcp.engines.git_history import GitHistoryEngine
from secscan_mcp.engines.gitleaks import GitleaksEngine
from secscan_mcp.normalize import Category, Finding, ScanReport, Severity, build_report
from secscan_mcp.paths import resolve_scan_path

DEFAULT_TIMEOUT = int(os.environ.get("SECSCAN_DEFAULT_TIMEOUT_SECONDS", "300"))
MAX_FINDINGS = int(os.environ.get("SECSCAN_MAX_FINDINGS", "500"))


@dataclass(frozen=True)
class ScannerStatus:
    name: str
    category: str
    installed: bool


def list_scanners() -> list[ScannerStatus]:
    return [
        ScannerStatus(name=e.name, category=e.category.value, installed=e.is_installed())
        for e in ALL_ENGINES
    ]


def _run_engine(
    engine: Engine, root: Path, timeout: int, **kwargs: object
) -> tuple[str, list[Finding], str | None]:
    if not engine.is_installed():
        return engine.name, [], None
    try:
        if isinstance(engine, GitleaksEngine | GitHistoryEngine):
            include_history = bool(kwargs.get("include_git_history", False))
            findings = engine.run(root, timeout=timeout, include_git_history=include_history)
        else:
            findings = engine.run(root, timeout=timeout)
        return engine.name, findings, None
    except Exception as exc:  # collect per-engine errors without failing the whole scan
        return engine.name, [], str(exc)


def _run_engines(
    engines: list[Engine],
    root: Path,
    *,
    timeout: int,
    **kwargs: object,
) -> tuple[list[Finding], list[str], list[str], list[str]]:
    findings: list[Finding] = []
    engines_run: list[str] = []
    engines_skipped = [e.name for e in engines if not e.is_installed()]
    errors: list[str] = []
    to_run = [e for e in engines if e.is_installed()]
    if not bool(kwargs.get("include_git_history", False)):
        to_run = [e for e in to_run if e.name != "git_history"]

    if not to_run:
        return findings, engines_run, engines_skipped, errors

    with ThreadPoolExecutor(max_workers=min(len(to_run), 4)) as pool:
        futures = {
            pool.submit(_run_engine, engine, root, timeout, **kwargs): engine for engine in to_run
        }
        for future in as_completed(futures):
            name, engine_findings, error = future.result()
            engines_run.append(name)
            if error:
                errors.append(f"{name}: {error}")
            findings.extend(engine_findings)

    if len(findings) > MAX_FINDINGS:
        findings = findings[:MAX_FINDINGS]
        errors.append(f"Results truncated to {MAX_FINDINGS} findings")

    return findings, engines_run, engines_skipped, errors


def scan(
    path: str | Path,
    *,
    categories: list[Category] | None = None,
    severity_threshold: Severity | None = None,
    timeout: int = DEFAULT_TIMEOUT,
    include_git_history: bool = False,
) -> ScanReport:
    root = resolve_scan_path(path)
    engines: list[Engine] = []
    if categories:
        for category in categories:
            engines.extend(ENGINES_BY_CATEGORY.get(category, []))
    else:
        engines = ALL_ENGINES

    findings, engines_run, engines_skipped, errors = _run_engines(
        engines,
        root,
        timeout=timeout,
        include_git_history=include_git_history,
    )
    return build_report(
        str(root),
        findings,
        engines_run=engines_run,
        engines_skipped=engines_skipped,
        errors=errors,
        severity_threshold=severity_threshold,
    )


def scan_secrets(
    path: str | Path,
    *,
    include_git_history: bool = False,
    severity_threshold: Severity | None = None,
    timeout: int = DEFAULT_TIMEOUT,
) -> ScanReport:
    return scan(
        path,
        categories=[Category.SECRET],
        severity_threshold=severity_threshold,
        timeout=timeout,
        include_git_history=include_git_history,
    )


def scan_code(
    path: str | Path,
    *,
    severity_threshold: Severity | None = None,
    timeout: int = DEFAULT_TIMEOUT,
) -> ScanReport:
    return scan(
        path,
        categories=[Category.SAST],
        severity_threshold=severity_threshold,
        timeout=timeout,
    )


def scan_dependencies(
    path: str | Path,
    *,
    severity_threshold: Severity | None = None,
    timeout: int = DEFAULT_TIMEOUT,
) -> ScanReport:
    return scan(
        path,
        categories=[Category.DEPENDENCY],
        severity_threshold=severity_threshold,
        timeout=timeout,
    )


def scan_iac(
    path: str | Path,
    *,
    severity_threshold: Severity | None = None,
    timeout: int = DEFAULT_TIMEOUT,
) -> ScanReport:
    return scan(
        path,
        categories=[Category.IAC],
        severity_threshold=severity_threshold,
        timeout=timeout,
    )


def report_to_json(report: ScanReport) -> str:
    return json.dumps(report.to_dict(), indent=2)


def parse_severity_threshold(value: str | None) -> Severity | None:
    if not value:
        return None
    try:
        return Severity(value.strip().lower())
    except ValueError as exc:
        msg = f"Invalid severity threshold: {value}"
        raise ValueError(msg) from exc
