"""Shared pytest fixtures."""

from __future__ import annotations

import subprocess
from pathlib import Path

import pytest


def _git(*args: str, cwd: Path) -> None:
    subprocess.run(["git", *args], cwd=cwd, check=True, capture_output=True, text=True)


@pytest.fixture
def git_repo_with_secret_in_history(tmp_path: Path) -> Path:
    """Git repo where a secret exists only in an old commit, not the working tree."""
    _git("init", cwd=tmp_path)
    _git("config", "user.email", "test@example.com", cwd=tmp_path)
    _git("config", "user.name", "Test User", cwd=tmp_path)

    config = tmp_path / "config.py"
    config.write_text('INTERNAL_API_KEY = "abc123xyz789secretkey"\n', encoding="utf-8")
    _git("add", "config.py", cwd=tmp_path)
    _git("commit", "-m", "add api key", cwd=tmp_path)

    config.write_text("# credentials removed\n", encoding="utf-8")
    _git("add", "config.py", cwd=tmp_path)
    _git("commit", "-m", "remove api key from working tree", cwd=tmp_path)

    return tmp_path
