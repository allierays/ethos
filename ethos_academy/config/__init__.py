"""Config domain — configuration, priorities, and thresholds."""

from ethos_academy.config.config import EthosConfig
from ethos_academy.config.priorities import PRIORITY_THRESHOLDS, get_threshold

__all__ = [
    "EthosConfig",
    "PRIORITY_THRESHOLDS",
    "get_threshold",
]
