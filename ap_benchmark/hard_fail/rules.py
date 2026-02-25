"""
Hard Fail Rules - Pattern-Based Automatic Failures

These rules can fail questions BEFORE the API call, saving time and money.
Each rule has a regex pattern and applies to specific question types.

Rule categories:
1. Absolute language in distractors
2. Recall-only questions
3. Structural violations (MSQ: not 2-3 correct, not 5 options)
"""

import re
from dataclasses import dataclass
from typing import List, Set, Pattern, Callable, Dict, Any


@dataclass
class HardFailRule:
    """A single hard fail rule."""
    name: str
    description: str
    pattern: Pattern
    applies_to: Set[str]  # Question types this applies to
    check_field: str  # Field to check: 'question', 'distractors', 'answer', 'all'
    severity: str = "critical"  # 'critical' or 'major'


# Absolute language patterns - these are rarely correct in AP questions
ABSOLUTE_LANGUAGE_PATTERNS = [
    r'\b(total|totally)\b',
    r'\b(complete|completely)\b',
    r'\b(immediate|immediately)\b',
    r'\b(all|every|each)\s+(of\s+the\s+)?(people|nations|countries|states|citizens)',
    r'\b(never|always)\b',
    r'\b(none\s+of|all\s+of)\b',
    r'\b(entirely|absolutely|perfectly)\b',
    r'\b(only|solely|exclusively)\b',
    r'\b(universal|universally)\b',
    r'\b(without\s+exception)\b',
]

# Recall-only question patterns - AP tests analysis, not just facts
RECALL_ONLY_PATTERNS = [
    r'^what\s+year\s+',
    r'^who\s+was\s+(the\s+)?',
    r'^when\s+did\s+',
    r'^where\s+was\s+',
    r'^in\s+what\s+year\s+',
    r'^what\s+date\s+',
    r'^name\s+the\s+',
    r'^identify\s+the\s+person\s+who\s+',
    r'^which\s+president\s+',
    r'^what\s+was\s+the\s+name\s+of\s+',
    r'^what\s+is\s+the\s+capital\s+',
    r'^who\s+wrote\s+',
    r'^who\s+invented\s+',
    r'^what\s+country\s+',
    r'^which\s+war\s+',
]

# Trivially obvious patterns - answers that give themselves away
GIVEAWAY_PATTERNS = [
    r'all\s+of\s+the\s+above',
    r'none\s+of\s+the\s+above',
    r'both\s+[ab]\s+and\s+[bc]',
    r'a\s+and\s+b(\s+only)?',
    r'options?\s+[a-d]\s+and\s+[a-d]',
]

# Missing explanation patterns
POOR_EXPLANATION_PATTERNS = [
    r'^(the\s+)?answer\s+is\s+[a-d]\.?$',
    r'^[a-d]\s+is\s+(the\s+)?(correct|right)\s+answer\.?$',
    r'^correct\.?$',
    r'^this\s+is\s+(the\s+)?(correct|right)\s+answer\.?$',
]


def _build_combined_pattern(patterns: List[str], flags: int = re.IGNORECASE) -> Pattern:
    """Build a single compiled pattern from multiple patterns."""
    combined = '|'.join(f'({p})' for p in patterns)
    return re.compile(combined, flags)


# Pre-compiled patterns for efficiency
ABSOLUTE_LANGUAGE_RE = _build_combined_pattern(ABSOLUTE_LANGUAGE_PATTERNS)
RECALL_ONLY_RE = _build_combined_pattern(RECALL_ONLY_PATTERNS)
GIVEAWAY_RE = _build_combined_pattern(GIVEAWAY_PATTERNS)
POOR_EXPLANATION_RE = _build_combined_pattern(POOR_EXPLANATION_PATTERNS)


# Define all hard fail rules
HARD_FAIL_RULES: List[HardFailRule] = [
    HardFailRule(
        name="absolute_language_in_distractors",
        description="Distractor contains absolute language (total, complete, never, etc.)",
        pattern=ABSOLUTE_LANGUAGE_RE,
        applies_to={"mcq", "msq"},
        check_field="distractors",
    ),
    HardFailRule(
        name="absolute_language_in_correct",
        description="Correct answer contains absolute language",
        pattern=ABSOLUTE_LANGUAGE_RE,
        applies_to={"mcq", "msq"},
        check_field="correct_answer",
        severity="major",  # Less severe - might be intentional
    ),
    HardFailRule(
        name="recall_only_question",
        description="Question tests recall only (What year..., Who was...)",
        pattern=RECALL_ONLY_RE,
        applies_to={"mcq", "msq", "fill-in"},
        check_field="question",
    ),
    HardFailRule(
        name="giveaway_answer_option",
        description="Answer option uses 'all of the above', 'none of the above', etc.",
        pattern=GIVEAWAY_RE,
        applies_to={"mcq", "msq"},
        check_field="all_options",
    ),
    HardFailRule(
        name="poor_explanation",
        description="Explanation is trivial or just restates the answer",
        pattern=POOR_EXPLANATION_RE,
        applies_to={"mcq", "msq", "fill-in", "match"},
        check_field="explanation",
    ),
]


def get_rules_for_type(question_type: str) -> List[HardFailRule]:
    """Get all rules that apply to a given question type."""
    return [rule for rule in HARD_FAIL_RULES if question_type in rule.applies_to]


def check_msq_structure(question_dict: Dict[str, Any]) -> List[str]:
    """
    Check MSQ-specific structural requirements.

    Returns list of rule names that failed.
    """
    failures = []

    # Check number of options
    options = question_dict.get("answer_options", [])
    if len(options) != 5:
        failures.append("msq_wrong_option_count")

    # Check number of correct answers
    answer = question_dict.get("answer", [])
    if isinstance(answer, str):
        # Parse "A, B" or "AB" format
        answer = [c for c in answer.upper() if c in "ABCDE"]

    if not isinstance(answer, list):
        answer = [answer]

    if len(answer) < 2 or len(answer) > 3:
        failures.append("msq_wrong_correct_count")

    return failures


def check_mcq_structure(question_dict: Dict[str, Any]) -> List[str]:
    """
    Check MCQ-specific structural requirements.

    Returns list of rule names that failed.
    """
    failures = []

    # Check number of options
    options = question_dict.get("answer_options", [])
    if len(options) != 4:
        failures.append("mcq_wrong_option_count")

    # Check single correct answer
    answer = question_dict.get("answer", "")
    if isinstance(answer, list) and len(answer) != 1:
        failures.append("mcq_multiple_answers")

    return failures


def check_explanation(question_dict: Dict[str, Any]) -> List[str]:
    """
    Check that explanation exists and is meaningful.

    Handles multiple formats:
    - Top-level 'explanation' or 'answer_explanation'
    - Fill-in: nested in answer[].answer_explanation
    - Match: top-level 'answer_explanation'

    Returns list of rule names that failed.
    """
    failures = []

    # Check top-level explanation fields first
    explanation = (
        question_dict.get("explanation", "") or
        question_dict.get("answer_explanation", "") or
        ""
    ).strip()

    # For fill-in questions, check nested explanations in answer array
    if not explanation:
        answer = question_dict.get("answer", [])
        if isinstance(answer, list):
            nested_explanations = []
            for ans in answer:
                if isinstance(ans, dict):
                    nested_exp = ans.get("answer_explanation", "") or ans.get("explanation", "")
                    if nested_exp:
                        nested_explanations.append(nested_exp.strip())
            if nested_explanations:
                explanation = " ".join(nested_explanations)

    # Check for missing explanation
    if not explanation:
        failures.append("missing_explanation")
        return failures

    # Check for too-short explanation (less than 50 chars is suspicious)
    if len(explanation) < 50:
        failures.append("explanation_too_short")

    return failures


# Structural check functions by type
STRUCTURAL_CHECKS: Dict[str, Callable[[Dict[str, Any]], List[str]]] = {
    "mcq": check_mcq_structure,
    "msq": check_msq_structure,
}

# Content checks that apply to all question types
CONTENT_CHECKS: Dict[str, Callable[[Dict[str, Any]], List[str]]] = {
    "mcq": check_explanation,
    "msq": check_explanation,
    "fill-in": check_explanation,
    "match": check_explanation,
}
