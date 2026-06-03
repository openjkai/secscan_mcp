"""Scanner engine registry."""

from __future__ import annotations

from secscan_mcp.engines.bandit import BanditEngine
from secscan_mcp.engines.base import Engine
from secscan_mcp.engines.checkov import CheckovEngine
from secscan_mcp.engines.custom import CustomSecretsEngine
from secscan_mcp.engines.gitleaks import GitleaksEngine
from secscan_mcp.engines.osv import OsvEngine
from secscan_mcp.engines.semgrep import SemgrepEngine
from secscan_mcp.normalize import Category

SECRET_ENGINES: list[Engine] = [
    CustomSecretsEngine(),
    GitleaksEngine(),
]

SAST_ENGINES: list[Engine] = [
    SemgrepEngine(),
    BanditEngine(),
]

DEPENDENCY_ENGINES: list[Engine] = [
    OsvEngine(),
]

IAC_ENGINES: list[Engine] = [
    CheckovEngine(),
]

ALL_ENGINES: list[Engine] = SECRET_ENGINES + SAST_ENGINES + DEPENDENCY_ENGINES + IAC_ENGINES

ENGINES_BY_CATEGORY: dict[Category, list[Engine]] = {
    Category.SECRET: SECRET_ENGINES,
    Category.SAST: SAST_ENGINES,
    Category.DEPENDENCY: DEPENDENCY_ENGINES,
    Category.IAC: IAC_ENGINES,
}
