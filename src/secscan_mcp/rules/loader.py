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
