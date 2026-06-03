"""Tests for custom regex secret scanner."""

from secscan_mcp.engines.custom import CustomSecretsEngine


def test_custom_finds_internal_api_key(tmp_path: object) -> None:
    root = tmp_path  # type: ignore[assignment]
    sample = root / "config.py"
    sample.write_text('INTERNAL_API_KEY = "abc123xyz789secretkey"\n', encoding="utf-8")

    engine = CustomSecretsEngine()
    findings = engine.run(root, timeout=30)

    assert len(findings) >= 1
    assert any(f.rule_id == "internal-api-key" for f in findings)
    assert "abc123xyz789secretkey" not in (findings[0].code_snippet or "")
