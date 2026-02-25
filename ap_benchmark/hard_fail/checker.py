"""
Hard Fail Checker - Pre-Evaluation Checks

Runs hard fail rules BEFORE making API calls. If any rule triggers,
the question fails immediately with score 0.0.

This saves API costs and provides fast feedback on common issues.
"""

from typing import Dict, Any, List
import re

from ..core.models import HardFailResult
from .rules import (
    HARD_FAIL_RULES,
    STRUCTURAL_CHECKS,
    CONTENT_CHECKS,
    get_rules_for_type,
    HardFailRule,
)


def _extract_distractors(question_dict: Dict[str, Any]) -> List[str]:
    """Extract distractor texts (wrong answers) from question."""
    options = question_dict.get("answer_options", [])
    correct_answer = question_dict.get("answer", "")

    # Normalize correct answer to list of keys
    if isinstance(correct_answer, str):
        correct_keys = set(c.upper() for c in correct_answer if c.isalpha())
    elif isinstance(correct_answer, list):
        correct_keys = set(str(a).upper() for a in correct_answer)
    else:
        correct_keys = set()

    distractors = []
    for opt in options:
        if isinstance(opt, dict):
            key = opt.get("key", "").upper()
            text = opt.get("text", "")
            if key not in correct_keys:
                distractors.append(text)
        elif isinstance(opt, str):
            distractors.append(opt)

    return distractors


def _extract_correct_answer_text(question_dict: Dict[str, Any]) -> str:
    """Extract the text of the correct answer."""
    options = question_dict.get("answer_options", [])
    correct_answer = question_dict.get("answer", "")

    # Normalize correct answer to list of keys
    if isinstance(correct_answer, str):
        correct_keys = set(c.upper() for c in correct_answer if c.isalpha())
    elif isinstance(correct_answer, list):
        correct_keys = set(str(a).upper() for a in correct_answer)
    else:
        return ""

    texts = []
    for opt in options:
        if isinstance(opt, dict):
            key = opt.get("key", "").upper()
            text = opt.get("text", "")
            if key in correct_keys:
                texts.append(text)

    return " ".join(texts)


def _extract_all_options_text(question_dict: Dict[str, Any]) -> str:
    """Extract all option texts combined."""
    options = question_dict.get("answer_options", [])
    texts = []
    for opt in options:
        if isinstance(opt, dict):
            texts.append(opt.get("text", ""))
        elif isinstance(opt, str):
            texts.append(opt)
    return " ".join(texts)


def _extract_explanation(question_dict: Dict[str, Any]) -> str:
    """Extract explanation text."""
    return (
        question_dict.get("explanation", "") or
        question_dict.get("answer_explanation", "") or
        ""
    )


def _check_rule(
    rule: HardFailRule,
    question_dict: Dict[str, Any]
) -> Dict[str, str] | None:
    """
    Check if a rule triggers for a question.

    Returns detail dict if triggered, None otherwise.
    """
    # Get text to check based on field
    if rule.check_field == "question":
        text = question_dict.get("question", "")
    elif rule.check_field == "distractors":
        distractors = _extract_distractors(question_dict)
        text = " ".join(distractors)
    elif rule.check_field == "correct_answer":
        text = _extract_correct_answer_text(question_dict)
    elif rule.check_field == "all_options":
        text = _extract_all_options_text(question_dict)
    elif rule.check_field == "explanation":
        text = _extract_explanation(question_dict)
    elif rule.check_field == "all":
        # Check all text content
        parts = [
            question_dict.get("question", ""),
            _extract_explanation(question_dict),
        ]
        for opt in question_dict.get("answer_options", []):
            if isinstance(opt, dict):
                parts.append(opt.get("text", ""))
        text = " ".join(parts)
    else:
        text = ""

    if not text:
        return None

    # Check pattern
    match = rule.pattern.search(text)
    if match:
        return {
            "rule": rule.name,
            "matched": match.group(),
            "context": text[max(0, match.start()-20):match.end()+20],
            "severity": rule.severity,
        }

    return None


class HardFailChecker:
    """
    Checker class for running hard fail rules.

    Can be customized by disabling specific rules.
    """

    def __init__(self, disabled_rules: set[str] | None = None):
        """
        Initialize checker.

        Args:
            disabled_rules: Set of rule names to disable
        """
        self.disabled_rules = disabled_rules or set()

    def check(
        self,
        question_dict: Dict[str, Any],
        question_type: str
    ) -> HardFailResult:
        """
        Check a question against all applicable hard fail rules.

        Args:
            question_dict: Question data
            question_type: Type of question

        Returns:
            HardFailResult with triggered rules
        """
        triggered_rules = []
        details = []

        # Run pattern-based rules
        for rule in get_rules_for_type(question_type):
            if rule.name in self.disabled_rules:
                continue

            detail = _check_rule(rule, question_dict)
            if detail:
                triggered_rules.append(rule.name)
                details.append(detail)

        # Run structural checks
        if question_type in STRUCTURAL_CHECKS:
            structural_failures = STRUCTURAL_CHECKS[question_type](question_dict)
            for failure in structural_failures:
                if failure not in self.disabled_rules:
                    triggered_rules.append(failure)
                    details.append({
                        "rule": failure,
                        "matched": "structural requirement",
                        "context": f"{question_type} structure validation failed",
                        "severity": "critical",
                    })

        # Run content checks (explanation, etc.)
        if question_type in CONTENT_CHECKS:
            content_failures = CONTENT_CHECKS[question_type](question_dict)
            for failure in content_failures:
                if failure not in self.disabled_rules:
                    triggered_rules.append(failure)
                    details.append({
                        "rule": failure,
                        "matched": "content requirement",
                        "context": f"{question_type} content validation failed",
                        "severity": "major",
                    })

        return HardFailResult(
            failed=len(triggered_rules) > 0,
            rules_triggered=triggered_rules,
            details=details,
        )


# Default checker instance
_default_checker = HardFailChecker()


def check_hard_fails(
    question_dict: Dict[str, Any],
    question_type: str
) -> HardFailResult:
    """
    Check a question against hard fail rules.

    Convenience function using the default checker.

    Args:
        question_dict: Question data
        question_type: Type of question

    Returns:
        HardFailResult with any triggered rules
    """
    return _default_checker.check(question_dict, question_type)


def get_all_rule_names() -> List[str]:
    """Get names of all hard fail rules."""
    rule_names = [rule.name for rule in HARD_FAIL_RULES]

    # Add structural check names
    for check_func in STRUCTURAL_CHECKS.values():
        # These are known structural checks
        rule_names.extend([
            "mcq_wrong_option_count",
            "mcq_multiple_answers",
            "msq_wrong_option_count",
            "msq_wrong_correct_count",
        ])

    return list(set(rule_names))
