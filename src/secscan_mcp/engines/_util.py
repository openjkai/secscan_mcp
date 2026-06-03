"""Shared helpers for engine adapters."""

from __future__ import annotations

import json
import logging
import shutil
import subprocess
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


def command_exists(name: str) -> bool:
    return shutil.which(name) is not None


def run_command(
    cmd: list[str],
    *,
    cwd: Path,
    timeout: int,
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        cmd,
        cwd=cwd,
        capture_output=True,
        text=True,
        timeout=timeout,
        check=False,
    )


def parse_json(stdout: str) -> Any:
    text = stdout.strip()
    if not text:
        return None
    return json.loads(text)
