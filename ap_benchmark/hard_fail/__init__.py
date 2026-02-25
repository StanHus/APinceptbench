"""Hard fail detection - pre-evaluation checks that can fail questions without API call."""

from .checker import check_hard_fails, HardFailChecker
from .rules import HARD_FAIL_RULES, HardFailRule

__all__ = [
    "check_hard_fails",
    "HardFailChecker",
    "HARD_FAIL_RULES",
    "HardFailRule",
]
