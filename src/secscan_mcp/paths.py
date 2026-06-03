"""Safe path resolution for scan targets."""

from __future__ import annotations

from pathlib import Path


class PathValidationError(ValueError):
    """Raised when a scan path is invalid or unsafe."""


def resolve_scan_path(path: str | Path) -> Path:
    """Resolve and validate a directory to scan."""
    candidate = Path(path).expanduser()
    try:
        resolved = candidate.resolve(strict=True)
    except FileNotFoundError as exc:
        msg = f"Path does not exist: {candidate}"
        raise PathValidationError(msg) from exc

    if not resolved.is_dir():
        msg = f"Path is not a directory: {resolved}"
        raise PathValidationError(msg)

    return resolved
