"""
Tests for AP Benchmark System

Run with: pytest ap_benchmark/tests/
"""

import pytest
from unittest.mock import patch, MagicMock

from ..core.models import (
    BenchmarkResult,
    DimensionScore,
    HardFailResult,
    QuestionType,
    Issue,
    CRITICAL_DIMENSIONS,
    NON_CRITICAL_DIMENSIONS,
)
from ..core.scorer import (
    calculate_overall_score,
    get_score_range,
    is_passing,
    validate_score,
    PASS_THRESHOLD,
)
from ..core.hash import hash_question, hash_question_dict, verify_hash
from ..hard_fail.checker import check_hard_fails
from ..hard_fail.rules import HARD_FAIL_RULES


class TestDimensionScore:
    """Tests for DimensionScore model."""

    def test_valid_binary_scores(self):
        """Binary scores (0.0 and 1.0) should be accepted."""
        score_pass = DimensionScore(score=1.0, reasoning="Pass")
        score_fail = DimensionScore(score=0.0, reasoning="Fail")

        assert score_pass.score == 1.0
        assert score_fail.score == 0.0

    def test_invalid_partial_scores(self):
        """Non-binary scores should raise validation error."""
        with pytest.raises(ValueError):
            DimensionScore(score=0.5, reasoning="Partial")

        with pytest.raises(ValueError):
            DimensionScore(score=0.85, reasoning="Partial")


class TestScorer:
    """Tests for deterministic scoring logic."""

    def test_perfect_score(self):
        """No failures should give perfect score."""
        score = calculate_overall_score(0, 0)
        assert score == 1.0
        assert is_passing(score)

    def test_one_non_critical_failure_passes(self):
        """One non-critical failure should still pass."""
        score = calculate_overall_score(0, 1)
        assert score >= PASS_THRESHOLD
        assert is_passing(score)

    def test_two_non_critical_failures_fails(self):
        """Two non-critical failures should fail."""
        score = calculate_overall_score(0, 2)
        assert score < PASS_THRESHOLD
        assert not is_passing(score)

    def test_one_critical_failure_fails(self):
        """One critical failure should always fail."""
        score = calculate_overall_score(1, 0)
        assert score < PASS_THRESHOLD
        assert not is_passing(score)
        assert 0.60 <= score <= 0.69

    def test_two_critical_failures_severe(self):
        """Two critical failures should give very low score."""
        score = calculate_overall_score(2, 0)
        assert score < 0.40
        assert not is_passing(score)

    def test_score_ranges(self):
        """Verify all scores fall within expected ranges."""
        test_cases = [
            (0, 0, 0.95, 1.00),
            (0, 1, 0.85, 0.89),
            (0, 2, 0.75, 0.84),
            (1, 0, 0.60, 0.69),
            (1, 1, 0.50, 0.59),
            (2, 0, 0.30, 0.39),
        ]

        for c, n, min_expected, max_expected in test_cases:
            score = calculate_overall_score(c, n)
            assert min_expected <= score <= max_expected, \
                f"C={c}, N={n}: score {score} not in [{min_expected}, {max_expected}]"

    def test_validate_score(self):
        """Test score validation against ranges."""
        assert validate_score(1.0, 0, 0)
        assert validate_score(0.87, 0, 1)
        assert not validate_score(0.95, 0, 1)  # Too high for C=0, N=1


class TestHashing:
    """Tests for question hashing."""

    def test_hash_consistency(self):
        """Same question should always produce same hash."""
        question = "What was the main cause of the Civil War?"
        hash1 = hash_question(question)
        hash2 = hash_question(question)
        assert hash1 == hash2

    def test_hash_different_questions(self):
        """Different questions should produce different hashes."""
        hash1 = hash_question("Question 1")
        hash2 = hash_question("Question 2")
        assert hash1 != hash2

    def test_hash_question_dict(self):
        """Test hashing question dictionaries."""
        q = {
            "question": "Test question",
            "answer": "A",
            "answer_options": [{"key": "A", "text": "Answer"}],
        }
        hash1 = hash_question_dict(q)
        hash2 = hash_question_dict(q)
        assert hash1 == hash2

    def test_verify_hash(self):
        """Test hash verification."""
        q = {"question": "Test", "answer": "A"}
        original_hash = hash_question_dict(q)

        assert verify_hash(q, original_hash)

        q["question"] = "Modified"
        assert not verify_hash(q, original_hash)


class TestHardFails:
    """Tests for hard fail detection."""

    def test_absolute_language_in_distractors(self):
        """Absolute language in distractors should trigger hard fail."""
        question = {
            "question": "What caused X?",
            "answer": "A",
            "answer_options": [
                {"key": "A", "text": "Economic factors"},
                {"key": "B", "text": "The government completely failed"},
                {"key": "C", "text": "Social changes"},
                {"key": "D", "text": "Political shifts"},
            ],
        }

        result = check_hard_fails(question, "mcq")
        assert result.failed
        assert "absolute_language_in_distractors" in result.rules_triggered

    def test_recall_only_question(self):
        """Recall-only questions should trigger hard fail."""
        question = {
            "question": "What year did the Declaration of Independence get signed?",
            "answer": "B",
            "answer_options": [
                {"key": "A", "text": "1774"},
                {"key": "B", "text": "1776"},
                {"key": "C", "text": "1778"},
                {"key": "D", "text": "1781"},
            ],
        }

        result = check_hard_fails(question, "mcq")
        assert result.failed
        assert "recall_only_question" in result.rules_triggered

    def test_valid_question_no_hard_fail(self):
        """Valid questions should not trigger hard fails."""
        question = {
            "question": "Which of the following best explains the economic impact of the Industrial Revolution?",
            "answer": "C",
            "answer_options": [
                {"key": "A", "text": "Rural populations increased significantly"},
                {"key": "B", "text": "Agricultural output declined steadily"},
                {"key": "C", "text": "Urban manufacturing became the dominant economic sector"},
                {"key": "D", "text": "International trade decreased due to new technologies"},
            ],
            "explanation": "The Industrial Revolution fundamentally transformed economies by shifting production from rural agriculture to urban manufacturing. This led to urbanization, new labor patterns, and the rise of factory systems that defined modern industrial economies.",
        }

        result = check_hard_fails(question, "mcq")
        assert not result.failed

    def test_msq_wrong_option_count(self):
        """MSQ with wrong option count should fail."""
        question = {
            "question": "Select all that apply:",
            "answer": ["A", "B"],
            "answer_options": [
                {"key": "A", "text": "Option 1"},
                {"key": "B", "text": "Option 2"},
                {"key": "C", "text": "Option 3"},
                {"key": "D", "text": "Option 4"},
            ],
        }

        result = check_hard_fails(question, "msq")
        assert result.failed
        assert "msq_wrong_option_count" in result.rules_triggered

    def test_msq_wrong_correct_count(self):
        """MSQ with wrong number of correct answers should fail."""
        question = {
            "question": "Select all that apply:",
            "answer": ["A"],  # Only 1 correct answer
            "answer_options": [
                {"key": "A", "text": "Option 1"},
                {"key": "B", "text": "Option 2"},
                {"key": "C", "text": "Option 3"},
                {"key": "D", "text": "Option 4"},
                {"key": "E", "text": "Option 5"},
            ],
        }

        result = check_hard_fails(question, "msq")
        assert result.failed
        assert "msq_wrong_correct_count" in result.rules_triggered


class TestBenchmarkResult:
    """Tests for BenchmarkResult model."""

    def _create_passing_result(self) -> BenchmarkResult:
        """Create a passing benchmark result."""
        passing_dim = DimensionScore(score=1.0, reasoning="Pass")
        return BenchmarkResult(
            question_hash="abc123",
            question_type=QuestionType.MCQ,
            prompt_version="test",
            issues=[],
            factual_accuracy=passing_dim,
            curriculum_alignment=passing_dim,
            cognitive_demand=passing_dim,
            distractor_quality=passing_dim,
            explanation_quality=passing_dim,
            clarity=passing_dim,
            difficulty_alignment=passing_dim,
            overall_score=1.0,
        )

    def test_passing_result(self):
        """Test that perfect scores pass."""
        result = self._create_passing_result()
        assert result.passed
        assert result.critical_failures == 0
        assert result.non_critical_failures == 0

    def test_critical_failure_detection(self):
        """Test critical failure counting."""
        failing_dim = DimensionScore(score=0.0, reasoning="Fail")
        passing_dim = DimensionScore(score=1.0, reasoning="Pass")

        result = BenchmarkResult(
            question_hash="abc123",
            question_type=QuestionType.MCQ,
            prompt_version="test",
            issues=[],
            factual_accuracy=failing_dim,  # Critical
            curriculum_alignment=passing_dim,
            cognitive_demand=passing_dim,
            distractor_quality=passing_dim,
            explanation_quality=passing_dim,
            clarity=passing_dim,
            difficulty_alignment=passing_dim,
            overall_score=0.65,
        )

        assert result.critical_failures == 1
        assert not result.passed

    def test_get_failed_dimensions(self):
        """Test failed dimension listing."""
        failing_dim = DimensionScore(score=0.0, reasoning="Fail")
        passing_dim = DimensionScore(score=1.0, reasoning="Pass")

        result = BenchmarkResult(
            question_hash="abc123",
            question_type=QuestionType.MCQ,
            prompt_version="test",
            issues=[],
            factual_accuracy=passing_dim,
            curriculum_alignment=passing_dim,
            cognitive_demand=failing_dim,
            distractor_quality=failing_dim,
            explanation_quality=passing_dim,
            clarity=passing_dim,
            difficulty_alignment=passing_dim,
            overall_score=0.79,
        )

        failed = result.get_failed_dimensions()
        assert "cognitive_demand" in failed
        assert "distractor_quality" in failed
        assert len(failed) == 2


class TestPassThreshold:
    """Tests for pass threshold consistency."""

    def test_pass_threshold_value(self):
        """Verify pass threshold is exactly 0.85."""
        assert PASS_THRESHOLD == 0.85

    def test_boundary_scores(self):
        """Test scores at the pass/fail boundary."""
        # Exactly at threshold should pass
        assert is_passing(0.85)

        # Just below should fail
        assert not is_passing(0.84)
        assert not is_passing(0.849)

        # Above should pass
        assert is_passing(0.86)
        assert is_passing(1.0)
