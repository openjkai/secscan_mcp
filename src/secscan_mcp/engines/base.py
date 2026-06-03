"""Engine adapter protocol."""

from __future__ import annotations

from pathlib import Path
from typing import Protocol

from secscan_mcp.normalize import Category, Finding


class Engine(Protocol):
    name: str
    category: Category

    def is_installed(self) -> bool:
        """Return True if the scanner CLI is available."""
        ...

    def run(self, root: Path, *, timeout: int) -> list[Finding]:
        """Run the scanner against root and return normalized findings."""
        ...
