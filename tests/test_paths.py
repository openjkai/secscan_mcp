"""Tests for path validation."""

import pytest

from secscan_mcp.paths import PathValidationError, resolve_scan_path


def test_resolve_scan_path_valid(tmp_path: object) -> None:
    resolved = resolve_scan_path(tmp_path)  # type: ignore[arg-type]
    assert resolved.is_dir()


def test_resolve_scan_path_missing() -> None:
    with pytest.raises(PathValidationError):
        resolve_scan_path("/nonexistent-path-secscan-xyz")
