"""Load bundled secret-scan rules."""

from __future__ import annotations

import re
from importlib import resources
from typing import Any

import yaml

_RULES_PATH = "custom_secrets.yaml"


def load_secret_rules() -> list[dict[str, Any]]:
    rules_file = resources.files("secscan_mcp.rules").joinpath(_RULES_PATH)
    raw = yaml.safe_load(rules_file.read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        return []
    rules = raw.get("rules", [])
    loaded: list[dict[str, Any]] = []
    for rule in rules:
        if not isinstance(rule, dict) or "pattern" not in rule:
            continue
        entry = dict(rule)
        entry["pattern"] = re.compile(str(rule["pattern"]))
        loaded.append(entry)
    return loaded


def rule_remediation_map() -> dict[str, str]:
    """Map rule_id → remediation text from bundled secret rules."""
    result: dict[str, str] = {}
    for rule in load_secret_rules():
        rule_id = rule.get("id")
        remediation = rule.get("remediation")
        if isinstance(rule_id, str) and isinstance(remediation, str):
            result[rule_id] = remediation
    return result
