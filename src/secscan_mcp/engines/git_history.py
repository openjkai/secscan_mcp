"""Git commit history secret scanner (requires git, no external CLI)."""

from __future__ import annotations

import os
import re
from dataclasses import dataclass
from pathlib import Path

from secscan_mcp.engines._util import command_exists, run_command
from secscan_mcp.normalize import (
    Category,
    Finding,
    Severity,
    make_finding_id,
    map_severity,
    redact_snippet,
)
from secscan_mcp.rules.loader import load_secret_rules

_DEFAULT_MAX_COMMITS = int(os.environ.get("SECSCAN_GIT_MAX_COMMITS", "500"))
_COMMIT_PREFIX = "COMMIT:"
_HUNK_RE = re.compile(r"^@@ -\d+(?:,\d+)? \+(\d+)(?:,\d+)? @@")


@dataclass(frozen=True)
class _CommitContext:
    sha: str
    date: str
    subject: str


class GitHistoryEngine:
    name = "git_history"
    category = Category.SECRET

    def is_installed(self) -> bool:
        return command_exists("git")

    def run(self, root: Path, *, timeout: int, include_git_history: bool = False) -> list[Finding]:
        if not include_git_history:
            return []
        if not _is_git_repo(root):
            return []

        rules = load_secret_rules()
        max_commits = _DEFAULT_MAX_COMMITS
        proc = run_command(
            [
                "git",
                "log",
                "-p",
                "--all",
                f"-n{max_commits}",
                "--no-color",
                "--no-ext-diff",
                f"--format={_COMMIT_PREFIX}%H|%aI|%s",
            ],
            cwd=root,
            timeout=timeout,
        )
        if proc.returncode != 0:
            msg = proc.stderr.strip() or proc.stdout.strip() or f"git log exited {proc.returncode}"
            raise RuntimeError(msg)

        return _parse_git_log(proc.stdout, rules)


def _is_git_repo(root: Path) -> bool:
    proc = run_command(["git", "rev-parse", "--git-dir"], cwd=root, timeout=30)
    return proc.returncode == 0


def _parse_git_log(raw: str, rules: list[dict[str, object]]) -> list[Finding]:
    findings: list[Finding] = []
    commit = _CommitContext(sha="", date="", subject="")
    current_file = ""
    new_line = 0

    for line in raw.splitlines():
        if line.startswith(_COMMIT_PREFIX):
            commit = _parse_commit_line(line)
            current_file = ""
            new_line = 0
            continue

        if line.startswith("diff --git "):
            current_file = _parse_diff_path(line)
            new_line = 0
            continue

        hunk_match = _HUNK_RE.match(line)
        if hunk_match:
            new_line = int(hunk_match.group(1))
            continue

        if not line.startswith("+") or line.startswith("+++"):
            if line.startswith("-") and not line.startswith("---"):
                continue
            if line.startswith(" ") and current_file:
                new_line += 1
            continue

        added = line[1:]
        if not current_file or not commit.sha:
            continue

        for rule in rules:
            pattern = rule["pattern"]
            if not isinstance(pattern, re.Pattern):
                continue
            match = pattern.search(added)
            if match is None:
                continue
            rule_id = str(rule["id"])
            short_sha = commit.sha[:7]
            findings.append(
                Finding(
                    id=make_finding_id(
                        engine="git_history",
                        rule_id=rule_id,
                        file=current_file,
                        line=new_line,
                        category=Category.SECRET,
                    ),
                    category=Category.SECRET,
                    severity=map_severity(
                        str(rule.get("severity", "high")),
                        default=Severity.HIGH,
                    ),
                    title=f"{rule.get('title', rule_id)} in git history ({short_sha})",
                    file=current_file,
                    line=new_line,
                    rule_id=rule_id,
                    engine="git_history",
                    code_snippet=redact_snippet(match.group(0)),
                    remediation=_history_remediation(rule, commit),
                    confidence="medium",
                )
            )
        new_line += 1

    return findings


def _parse_commit_line(line: str) -> _CommitContext:
    payload = line[len(_COMMIT_PREFIX) :]
    parts = payload.split("|", 2)
    if len(parts) < 3:
        return _CommitContext(sha=payload, date="", subject="")
    return _CommitContext(sha=parts[0], date=parts[1], subject=parts[2])


def _parse_diff_path(line: str) -> str:
    # diff --git a/path b/path
    parts = line.split()
    if len(parts) >= 4 and parts[2].startswith("a/"):
        return parts[2][2:]
    if len(parts) >= 3 and parts[-1].startswith("b/"):
        return parts[-1][2:]
    return ""


def _history_remediation(rule: dict[str, object], commit: _CommitContext) -> str:
    base = str(rule.get("remediation", "")).strip()
    short_sha = commit.sha[:7] if commit.sha else "unknown"
    history = (
        f"Found in commit {short_sha}"
        + (f" ({commit.date})" if commit.date else "")
        + (f': "{commit.subject}"' if commit.subject else "")
        + ". Secrets in git history remain exposed even after deletion from the working tree. "
        "Rotate the credential and rewrite history (e.g. git filter-repo) or treat the secret as compromised."
    )
    return f"{base} {history}".strip() if base else history
