"""Tests for scan runner."""

from secscan_mcp.runner import list_scanners, scan_secrets


def test_list_scanners_includes_custom() -> None:
    names = {s.name for s in list_scanners()}
    assert "custom" in names


def test_scan_secrets_custom_only(tmp_path: object) -> None:
    root = tmp_path  # type: ignore[assignment]
    (root / "leak.py").write_text(
        'INTERNAL_API_KEY = "' + ("a" * 20) + '"\n',
        encoding="utf-8",
    )

    report = scan_secrets(root, timeout=30)
    assert report.summary.total >= 1
    assert "custom" in report.engines_run
