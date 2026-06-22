"""Tests for bundled secret rule loading."""

from secscan_mcp.rules.loader import load_secret_rules, rule_remediation_map


def test_load_secret_rules_has_patterns() -> None:
    rules = load_secret_rules()
    assert len(rules) >= 3
    assert all("pattern" in r and hasattr(r["pattern"], "search") for r in rules)


def test_rule_remediation_map_from_yaml() -> None:
    remediations = rule_remediation_map()
    assert "internal-api-key" in remediations
    assert "hardcoded-jwt" in remediations
    assert "generic-private-key-header" in remediations
    assert "environment" in remediations["internal-api-key"].lower()
