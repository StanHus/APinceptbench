"""
Deterministic Scoring - Lookup Table Based

Calculates overall score based on critical failures (C) and non-critical failures (N).
NO ambiguity, NO floating point comparison issues. Pure lookup table.

Scoring Table:
| C | N   | Score Range | Result |
|---|-----|-------------|--------|
| 0 | 0   | 0.95-1.00   | PASS   |
| 0 | 1   | 0.85-0.89   | PASS   |
| 0 | 2   | 0.75-0.84   | FAIL   |
| 0 | 3+  | 0.65-0.74   | FAIL   |
| 1 | 0   | 0.60-0.69   | FAIL   |
| 1 | 1   | 0.50-0.59   | FAIL   |
| 1 | 2+  | 0.40-0.49   | FAIL   |
| 2 | any | 0.00-0.39   | FAIL   |

Pass threshold: 0.85 (fixed, never changes)
"""

from typing import Tuple

# Fixed pass threshold - NEVER CHANGE THIS
PASS_THRESHOLD = 0.85


def calculate_overall_score(critical_failures: int, non_critical_failures: int) -> float:
    """
    Calculate overall score from failure counts.

    Uses deterministic lookup table. Within each range, the exact score
    is calculated based on the number of failures to provide granularity.

    Args:
        critical_failures: Count of critical dimension failures (0-2)
        non_critical_failures: Count of non-critical dimension failures (0-5)

    Returns:
        Overall score between 0.0 and 1.0
    """
    # Clamp inputs to valid ranges
    c = min(max(critical_failures, 0), 2)
    n = min(max(non_critical_failures, 0), 5)

    # Lookup table: (C, N) -> (base_score, penalty_per_additional_n)
    # The base score is the high end of the range, penalty reduces within range

    if c == 0:
        # No critical failures - can still pass
        if n == 0:
            # Perfect: 0.95-1.00
            return 1.00
        elif n == 1:
            # One minor issue: 0.85-0.89 (still passing)
            return 0.87
        elif n == 2:
            # Two minor issues: 0.75-0.84 (failing)
            return 0.79
        elif n == 3:
            # Three minor issues: 0.70-0.74
            return 0.72
        elif n == 4:
            # Four minor issues: 0.65-0.69
            return 0.67
        else:  # n >= 5
            # Many minor issues: 0.60-0.64
            return 0.62

    elif c == 1:
        # One critical failure - automatic fail
        if n == 0:
            # Critical only: 0.60-0.69
            return 0.65
        elif n == 1:
            # Critical + 1 minor: 0.50-0.59
            return 0.55
        elif n == 2:
            # Critical + 2 minor: 0.45-0.49
            return 0.47
        else:  # n >= 3
            # Critical + many minor: 0.40-0.44
            return 0.42

    else:  # c >= 2
        # Two critical failures - severe fail
        if n == 0:
            # Two critical only: 0.30-0.39
            return 0.35
        elif n == 1:
            # Two critical + 1 minor: 0.20-0.29
            return 0.25
        elif n == 2:
            # Two critical + 2 minor: 0.10-0.19
            return 0.15
        else:  # n >= 3
            # Two critical + many minor: 0.00-0.09
            return 0.05


def get_score_range(critical_failures: int, non_critical_failures: int) -> Tuple[float, float]:
    """
    Get the valid score range for given failure counts.

    Useful for validation and testing.

    Args:
        critical_failures: Count of critical dimension failures
        non_critical_failures: Count of non-critical dimension failures

    Returns:
        Tuple of (min_score, max_score) for this failure combination
    """
    c = min(max(critical_failures, 0), 2)
    n = min(max(non_critical_failures, 0), 5)

    if c == 0:
        if n == 0:
            return (0.95, 1.00)
        elif n == 1:
            return (0.85, 0.89)
        elif n == 2:
            return (0.75, 0.84)
        elif n == 3:
            return (0.70, 0.74)
        elif n == 4:
            return (0.65, 0.69)
        else:
            return (0.60, 0.64)
    elif c == 1:
        if n == 0:
            return (0.60, 0.69)
        elif n == 1:
            return (0.50, 0.59)
        elif n == 2:
            return (0.45, 0.49)
        else:
            return (0.40, 0.44)
    else:
        if n == 0:
            return (0.30, 0.39)
        elif n == 1:
            return (0.20, 0.29)
        elif n == 2:
            return (0.10, 0.19)
        else:
            return (0.00, 0.09)


def is_passing(score: float) -> bool:
    """
    Check if a score is passing.

    Args:
        score: Overall score

    Returns:
        True if score >= PASS_THRESHOLD
    """
    return score >= PASS_THRESHOLD


def validate_score(
    score: float,
    critical_failures: int,
    non_critical_failures: int
) -> bool:
    """
    Validate that a score is within the expected range for given failures.

    Args:
        score: Score to validate
        critical_failures: Count of critical failures
        non_critical_failures: Count of non-critical failures

    Returns:
        True if score is within valid range
    """
    min_score, max_score = get_score_range(critical_failures, non_critical_failures)
    return min_score <= score <= max_score


def explain_score(critical_failures: int, non_critical_failures: int) -> str:
    """
    Generate human-readable explanation of score calculation.

    Args:
        critical_failures: Count of critical failures
        non_critical_failures: Count of non-critical failures

    Returns:
        Explanation string
    """
    score = calculate_overall_score(critical_failures, non_critical_failures)
    passing = "PASS" if is_passing(score) else "FAIL"
    min_s, max_s = get_score_range(critical_failures, non_critical_failures)

    if critical_failures == 0:
        if non_critical_failures == 0:
            reason = "No failures detected - perfect score"
        elif non_critical_failures == 1:
            reason = "One non-critical issue - still acceptable"
        else:
            reason = f"{non_critical_failures} non-critical issues - too many minor problems"
    elif critical_failures == 1:
        if non_critical_failures == 0:
            reason = "One critical failure - automatic fail"
        else:
            reason = f"One critical failure + {non_critical_failures} non-critical issues"
    else:
        reason = f"Two critical failures - severe quality issues"

    return (
        f"Score: {score:.2f} ({passing})\n"
        f"Critical failures: {critical_failures}\n"
        f"Non-critical failures: {non_critical_failures}\n"
        f"Valid range: [{min_s:.2f}, {max_s:.2f}]\n"
        f"Reason: {reason}"
    )
