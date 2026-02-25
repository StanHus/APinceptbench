"""
AP Benchmark System - Independent Evaluation for AP Social Studies Questions

A self-contained, deterministic benchmark system that uses Claude as an
independent evaluator. Follows InceptBench methodology for reproducible results.

KEY PRINCIPLE: The original REQUEST is the ground truth.
Questions are evaluated against what was requested, not in isolation.

Features:
- Request-centric evaluation (evaluates response against original request)
- Image evaluation support (uses Claude vision)
- Binary metrics only (0.0 or 1.0, no partial credit)
- Hard fail rules (auto-reject bad questions before API call)
- Deterministic scoring (temperature=0.0)

Usage:
    python -m ap_benchmark --input questions.json
    python -m ap_benchmark --calibrate
    python -m ap_benchmark --input questions.json --format markdown
"""

__version__ = "1.1.0"
__prompt_version__ = "2026.02.23.3"  # Update when prompts change

from .core.models import (
    BenchmarkResult,
    DimensionScore,
    HardFailResult,
    QuestionType,
    EvaluationRequest,
)
from .core.evaluator import evaluate_question, evaluate_batch, evaluate_with_request
from .core.scorer import calculate_overall_score, PASS_THRESHOLD
from .hard_fail.checker import check_hard_fails

__all__ = [
    "BenchmarkResult",
    "DimensionScore",
    "HardFailResult",
    "QuestionType",
    "EvaluationRequest",
    "evaluate_question",
    "evaluate_batch",
    "evaluate_with_request",
    "calculate_overall_score",
    "check_hard_fails",
    "PASS_THRESHOLD",
]
