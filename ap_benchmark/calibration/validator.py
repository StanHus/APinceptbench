"""
Calibration Validator - Evaluator Accuracy Checker

Validates the evaluator against the gold standard calibration set.
Ensures >= 95% accuracy to catch evaluator drift over time.

Usage:
    from ap_benchmark.calibration import validate_evaluator
    result = validate_evaluator()
    assert result.accuracy >= 0.95
"""

import json
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple

from ..core.evaluator import evaluate_question
from ..core.models import BenchmarkResult
from ..core.scorer import PASS_THRESHOLD


@dataclass
class CalibrationExample:
    """A single calibration example."""
    id: str
    expected_pass: bool
    expected_score_range: Tuple[float, float]
    question_dict: Dict[str, Any]
    expected_failures: List[str] = field(default_factory=list)
    failure_reason: str = ""


@dataclass
class ValidationResult:
    """Result of validating a single example."""
    example_id: str
    expected_pass: bool
    actual_pass: bool
    expected_score_range: Tuple[float, float]
    actual_score: float
    correct: bool
    score_in_range: bool
    expected_failures: List[str]
    actual_failures: List[str]
    message: str


@dataclass
class CalibrationResult:
    """Overall calibration result."""
    total_examples: int
    correct_count: int
    accuracy: float
    results: List[ValidationResult]
    passed: bool
    required_accuracy: float = 0.95

    @property
    def failed_examples(self) -> List[ValidationResult]:
        """Get examples that were incorrectly evaluated."""
        return [r for r in self.results if not r.correct]


def load_gold_standard() -> List[CalibrationExample]:
    """Load the gold standard calibration set."""
    # Find the gold_standard.json file
    calibration_dir = Path(__file__).parent
    gold_standard_path = calibration_dir / "gold_standard.json"

    if not gold_standard_path.exists():
        raise FileNotFoundError(f"Gold standard file not found: {gold_standard_path}")

    with open(gold_standard_path, 'r') as f:
        data = json.load(f)

    examples = []
    for ex in data.get("examples", []):
        # Build question dict
        question_dict = {
            "question": ex.get("question", ""),
            "answer": ex.get("answer"),
            "answer_options": ex.get("answer_options", []),
            "explanation": ex.get("explanation", ""),
            "type": ex.get("type", "mcq"),
        }

        examples.append(CalibrationExample(
            id=ex.get("id", ""),
            expected_pass=ex.get("expected_pass", True),
            expected_score_range=tuple(ex.get("expected_score_range", [0.0, 1.0])),
            question_dict=question_dict,
            expected_failures=ex.get("expected_failures", []),
            failure_reason=ex.get("failure_reason", ""),
        ))

    return examples


def validate_example(example: CalibrationExample) -> ValidationResult:
    """
    Validate a single calibration example.

    Args:
        example: CalibrationExample to validate

    Returns:
        ValidationResult with comparison details
    """
    # Evaluate the question
    try:
        result = evaluate_question(
            question_dict=example.question_dict,
            question_type=example.question_dict.get("type", "mcq"),
            difficulty=example.question_dict.get("difficulty", "medium"),
            curriculum_info=example.question_dict.get("curriculum_info", ""),
        )

        actual_pass = result.passed
        actual_score = result.overall_score
        actual_failures = result.get_failed_dimensions()

    except Exception as e:
        # Evaluation error - count as incorrect
        return ValidationResult(
            example_id=example.id,
            expected_pass=example.expected_pass,
            actual_pass=False,
            expected_score_range=example.expected_score_range,
            actual_score=0.0,
            correct=False,
            score_in_range=False,
            expected_failures=example.expected_failures,
            actual_failures=[],
            message=f"Evaluation error: {str(e)}"
        )

    # Check if pass/fail matches
    correct = actual_pass == example.expected_pass

    # Check if score is in expected range
    min_score, max_score = example.expected_score_range
    score_in_range = min_score <= actual_score <= max_score

    # Build message
    if correct and score_in_range:
        message = "Correct"
    elif not correct:
        message = f"Wrong pass/fail: expected {'PASS' if example.expected_pass else 'FAIL'}, got {'PASS' if actual_pass else 'FAIL'}"
    else:
        message = f"Score out of range: expected [{min_score:.2f}, {max_score:.2f}], got {actual_score:.2f}"

    return ValidationResult(
        example_id=example.id,
        expected_pass=example.expected_pass,
        actual_pass=actual_pass,
        expected_score_range=example.expected_score_range,
        actual_score=actual_score,
        correct=correct,
        score_in_range=score_in_range,
        expected_failures=example.expected_failures,
        actual_failures=actual_failures,
        message=message,
    )


def validate_evaluator(
    required_accuracy: float = 0.95,
    verbose: bool = False,
    progress_callback: Optional[callable] = None,
) -> CalibrationResult:
    """
    Validate the evaluator against the gold standard.

    Args:
        required_accuracy: Minimum accuracy to pass (default 0.95 = 95%)
        verbose: If True, print progress information
        progress_callback: Optional callback(current, total) for progress

    Returns:
        CalibrationResult with overall accuracy and per-example results
    """
    # Load examples
    examples = load_gold_standard()
    total = len(examples)

    if verbose:
        print(f"Validating evaluator against {total} calibration examples...")

    results = []
    correct_count = 0

    for i, example in enumerate(examples):
        result = validate_example(example)
        results.append(result)

        if result.correct:
            correct_count += 1

        if verbose:
            status = "PASS" if result.correct else "FAIL"
            print(f"  [{i+1}/{total}] {example.id}: {status} - {result.message}")

        if progress_callback:
            progress_callback(i + 1, total)

    accuracy = correct_count / total if total > 0 else 0.0
    passed = accuracy >= required_accuracy

    if verbose:
        print(f"\nAccuracy: {accuracy:.1%} ({correct_count}/{total})")
        print(f"Required: {required_accuracy:.1%}")
        print(f"Result: {'PASSED' if passed else 'FAILED'}")

        if not passed:
            print("\nFailed examples:")
            for r in results:
                if not r.correct:
                    print(f"  - {r.example_id}: {r.message}")

    return CalibrationResult(
        total_examples=total,
        correct_count=correct_count,
        accuracy=accuracy,
        results=results,
        passed=passed,
        required_accuracy=required_accuracy,
    )


def quick_validate(sample_size: int = 5) -> bool:
    """
    Quick validation with a subset of examples.

    Useful for fast smoke tests.

    Args:
        sample_size: Number of examples to test

    Returns:
        True if all sampled examples pass
    """
    examples = load_gold_standard()

    # Take first N good and first N bad
    good = [e for e in examples if e.expected_pass][:sample_size // 2 + 1]
    bad = [e for e in examples if not e.expected_pass][:sample_size // 2 + 1]
    sample = good + bad

    for example in sample:
        result = validate_example(example)
        if not result.correct:
            return False

    return True
