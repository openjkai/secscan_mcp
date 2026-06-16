"""Integration tests that invoke optional external scanner CLIs."""

from __future__ import annotations

import shutil

import pytest

from secscan_mcp.engines.gitleaks import GitleaksEngine
from secscan_mcp.runner import scan_secrets

pytestmark = pytest.mark.integration


@pytest.mark.skipif(shutil.which("gitleaks") is None, reason="gitleaks not installed")
def test_gitleaks_scans_working_tree(tmp_path: object) -> None:
    root = tmp_path  # type: ignore[assignment]
    (root / "leak.env").write_text(
        'AWS_SECRET_ACCESS_KEY="wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY"\n',
        encoding="utf-8",
    )

    report = scan_secrets(root, timeout=120)
    assert "gitleaks" in report.engines_run
    assert report.summary.total >= 1


@pytest.mark.skipif(shutil.which("gitleaks") is None, reason="gitleaks not installed")
def test_gitleaks_scans_git_history(git_repo_with_secret_in_history: object) -> None:
    root = git_repo_with_secret_in_history  # type: ignore[assignment]

    report = scan_secrets(root, include_git_history=True, timeout=120)
    assert "gitleaks" in report.engines_run
    assert report.summary.total >= 1


def test_gitleaks_engine_reports_install_status() -> None:
    engine = GitleaksEngine()
    assert engine.is_installed() is (shutil.which("gitleaks") is not None)
