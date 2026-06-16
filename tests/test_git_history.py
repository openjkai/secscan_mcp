"""Tests for git commit history secret scanner."""

from __future__ import annotations

import shutil

import pytest

from secscan_mcp.engines.git_history import GitHistoryEngine, _parse_git_log
from secscan_mcp.rules.loader import load_secret_rules
from secscan_mcp.runner import scan_secrets

pytestmark = pytest.mark.skipif(shutil.which("git") is None, reason="git not installed")


def test_parse_git_log_finds_secret_in_patch() -> None:
    raw = """COMMIT:abc123def456789012345678901234567890abcd|2024-01-01T00:00:00+00:00|add key

diff --git a/config.py b/config.py
--- a/config.py
+++ b/config.py
@@ -0,0 +1 @@
+INTERNAL_API_KEY = "abc123xyz789secretkey"
"""
    findings = _parse_git_log(raw, load_secret_rules())
    assert len(findings) == 1
    assert findings[0].engine == "git_history"
    assert findings[0].rule_id == "internal-api-key"
    assert findings[0].file == "config.py"
    assert "abc123xyz789secretkey" not in findings[0].code_snippet
    assert "abc123d" in findings[0].remediation


def test_git_history_finds_removed_secret(git_repo_with_secret_in_history: object) -> None:
    root = git_repo_with_secret_in_history  # type: ignore[assignment]
    engine = GitHistoryEngine()
    assert engine.is_installed()

    without_history = engine.run(root, timeout=30, include_git_history=False)
    assert without_history == []

    with_history = engine.run(root, timeout=30, include_git_history=True)
    assert len(with_history) >= 1
    assert any(f.rule_id == "internal-api-key" for f in with_history)


def test_scan_secrets_include_git_history(git_repo_with_secret_in_history: object) -> None:
    root = git_repo_with_secret_in_history  # type: ignore[assignment]

    current_only = scan_secrets(root, include_git_history=False, timeout=30)
    assert current_only.summary.total == 0

    with_history = scan_secrets(root, include_git_history=True, timeout=30)
    assert with_history.summary.total >= 1
    assert "git_history" in with_history.engines_run
