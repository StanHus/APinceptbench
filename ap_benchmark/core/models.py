"""
Benchmark Models - Binary Metrics Only

Pydantic models for the AP Benchmark system. All dimension scores are binary
(0.0 = fail, 1.0 = pass) to force clear decisions and prevent wishy-washy scoring.

KEY PRINCIPLE: The benchmark evaluates responses AGAINST the original request.
The request (substandard, skills, difficulty) is the ground truth.

Pass threshold: 0.85 (fixed, never changes)
"""

from enum import Enum
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, field_validator, computed_field


class QuestionType(str, Enum):
    """Types of questions we evaluate."""
    MCQ = "mcq"
    MSQ = "msq"
    FILL_IN = "fill-in"
    MATCH = "match"
    ARTICLE = "article"


class EvaluationRequest(BaseModel):
    """
    The original request that generated the content.

    This is the GROUND TRUTH against which responses are evaluated.
    A response that doesn't match the request FAILS curriculum_alignment.
    """
    substandard_id: str = Field(..., description="e.g., 'AP.USH.3.1'")
    node_id: Optional[str] = Field(None, description="MongoDB node_id (e.g., 'KC-1.1.I.A')")
    substandard_description: Optional[str] = Field(None, description="What skill/concept to test")
    difficulty: str = Field("medium", description="easy, medium, hard")
    question_type: str = Field("mcq", description="mcq, msq, fill-in, match, article")
    lesson_title: Optional[str] = Field(None, description="Lesson context")
    instructions: Optional[str] = Field(None, description="Additional generation instructions")

    def get_curriculum_context(self) -> str:
        """Build curriculum context string for evaluation prompt."""
        parts = [f"Substandard: {self.substandard_id}"]
        if self.substandard_description:
            parts.append(f"Skill/Concept: {self.substandard_description}")
        if self.lesson_title:
            parts.append(f"Lesson: {self.lesson_title}")
        parts.append(f"Required Difficulty: {self.difficulty}")
        parts.append(f"Required Type: {self.question_type}")
        if self.instructions:
            parts.append(f"Special Instructions: {self.instructions}")
        return "\n".join(parts)


class Issue(BaseModel):
    """
    A specific issue identified during evaluation.

    Issues are identified BEFORE scoring. Each issue maps to one or more
    dimensions that should fail as a result.
    """
    id: str = Field(..., description="Issue ID (e.g., ISSUE1, ISSUE2)")
    dimension: str = Field(..., description="Primary dimension this issue affects")
    snippet: str = Field(..., description="Exact problematic text/content")
    explanation: str = Field(..., description="Why this violates the dimension")
    severity: str = Field("major", description="major or minor")


class DimensionScore(BaseModel):
    """
    Score for a single evaluation dimension.

    BINARY ONLY: score must be exactly 0.0 or 1.0.
    No partial credit - forces clear pass/fail decisions.
    """
    score: float = Field(..., description="0.0 (fail) or 1.0 (pass)")
    reasoning: str = Field(..., description="Why this dimension passed or failed")
    issues: List[str] = Field(
        default_factory=list,
        description="Issue IDs that caused this dimension to fail"
    )

    @field_validator('score')
    @classmethod
    def validate_binary(cls, v: float) -> float:
        """Enforce binary scoring - no partial credit."""
        if v not in (0.0, 1.0):
            raise ValueError(f"Score must be exactly 0.0 or 1.0, got {v}")
        return v


class HardFailResult(BaseModel):
    """
    Result of pre-evaluation hard fail checks.

    Hard fails are automatic failures detected before calling the API,
    such as absolute language in distractors or recall-only questions.
    """
    failed: bool = Field(..., description="True if any hard fail rule triggered")
    rules_triggered: List[str] = Field(
        default_factory=list,
        description="Names of hard fail rules that triggered"
    )
    details: List[Dict[str, str]] = Field(
        default_factory=list,
        description="Details about each triggered rule"
    )


# Critical dimensions - failures here have severe impact on overall score
CRITICAL_DIMENSIONS = {"factual_accuracy", "curriculum_alignment"}

# Non-critical dimensions - failures have less severe impact
NON_CRITICAL_DIMENSIONS = {
    "cognitive_demand",
    "distractor_quality",
    "explanation_quality",
    "clarity",
    "difficulty_alignment",
}


class BenchmarkResult(BaseModel):
    """
    Complete benchmark result for a question.

    Binary metrics only. Overall score is calculated deterministically
    from critical failures (C) and non-critical failures (N):

    | C | N   | Score Range |
    |---|-----|-------------|
    | 0 | 0   | 0.95-1.00   | PASS
    | 0 | 1   | 0.85-0.89   | PASS
    | 0 | 2   | 0.75-0.84   | FAIL
    | 1 | any | 0.40-0.69   | FAIL
    | 2 | any | 0.00-0.39   | FAIL

    Pass threshold: 0.85 (fixed)
    """

    # Metadata
    question_hash: str = Field(..., description="SHA256 hash for reproducibility")
    question_type: QuestionType
    prompt_version: str = Field(..., description="Version of evaluation prompt used")

    # Hard fail result (if any)
    hard_fail: Optional[HardFailResult] = None

    # Issues identified (populated BEFORE scoring)
    issues: List[Issue] = Field(default_factory=list)

    # Critical dimensions (binary)
    factual_accuracy: DimensionScore = Field(
        ..., description="All facts correct, answer properly labeled"
    )
    curriculum_alignment: DimensionScore = Field(
        ..., description="Aligns with AP curriculum standards"
    )

    # Non-critical dimensions (binary)
    cognitive_demand: DimensionScore = Field(
        ..., description="Requires analysis/synthesis, not just recall"
    )
    distractor_quality: DimensionScore = Field(
        ..., description="Plausible distractors based on common misconceptions"
    )
    explanation_quality: DimensionScore = Field(
        ..., description="Answer explanation is thorough and educational"
    )
    clarity: DimensionScore = Field(
        ..., description="Clear, unambiguous wording"
    )
    difficulty_alignment: DimensionScore = Field(
        ..., description="Appropriate for stated difficulty level"
    )

    # Calculated fields
    overall_score: float = Field(..., ge=0.0, le=1.0)

    @computed_field
    @property
    def passed(self) -> bool:
        """Whether the question passes (score >= 0.85)."""
        return self.overall_score >= 0.85

    @computed_field
    @property
    def critical_failures(self) -> int:
        """Count of critical dimension failures."""
        count = 0
        if self.factual_accuracy.score == 0.0:
            count += 1
        if self.curriculum_alignment.score == 0.0:
            count += 1
        return count

    @computed_field
    @property
    def non_critical_failures(self) -> int:
        """Count of non-critical dimension failures."""
        count = 0
        for dim in [
            self.cognitive_demand,
            self.distractor_quality,
            self.explanation_quality,
            self.clarity,
            self.difficulty_alignment,
        ]:
            if dim.score == 0.0:
                count += 1
        return count

    def get_failed_dimensions(self) -> List[str]:
        """Get list of dimension names that failed."""
        failed = []
        dimensions = {
            'factual_accuracy': self.factual_accuracy,
            'curriculum_alignment': self.curriculum_alignment,
            'cognitive_demand': self.cognitive_demand,
            'distractor_quality': self.distractor_quality,
            'explanation_quality': self.explanation_quality,
            'clarity': self.clarity,
            'difficulty_alignment': self.difficulty_alignment,
        }
        for name, dim in dimensions.items():
            if dim.score == 0.0:
                failed.append(name)
        return failed

    def validate_consistency(self) -> List[str]:
        """
        Validate self-consistency: every 0.0 has issues, every issue has 0.0.

        Returns list of inconsistency warnings (empty if consistent).
        """
        warnings = []

        # Map issue IDs to dimensions
        issue_dimensions = {issue.id: issue.dimension for issue in self.issues}

        # Check: every 0.0 dimension should have at least one issue
        for dim_name in self.get_failed_dimensions():
            has_issue = any(
                dim_name in (issue.dimension, *dim.issues)
                for issue in self.issues
                for dim in [getattr(self, dim_name)]
            )
            if not has_issue and not getattr(self, dim_name).issues:
                warnings.append(f"Dimension '{dim_name}' failed but has no associated issues")

        # Check: every issue should have a corresponding 0.0 dimension
        for issue in self.issues:
            dim = getattr(self, issue.dimension, None)
            if dim and dim.score == 1.0:
                warnings.append(
                    f"Issue '{issue.id}' affects '{issue.dimension}' but that dimension passed"
                )

        return warnings

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return self.model_dump()

    def to_json(self) -> str:
        """Convert to JSON string."""
        return self.model_dump_json(indent=2)


class BatchResult(BaseModel):
    """Result of batch evaluation."""
    total_count: int
    evaluated_count: int
    hard_fail_count: int
    pass_count: int
    fail_count: int
    results: Dict[str, BenchmarkResult] = Field(
        default_factory=dict,
        description="question_id -> result"
    )
    errors: List[Dict[str, str]] = Field(default_factory=list)

    @computed_field
    @property
    def pass_rate(self) -> float:
        """Percentage of evaluated questions that passed."""
        if self.evaluated_count == 0:
            return 0.0
        return self.pass_count / self.evaluated_count

    @computed_field
    @property
    def average_score(self) -> float:
        """Average overall score of evaluated questions."""
        if not self.results:
            return 0.0
        return sum(r.overall_score for r in self.results.values()) / len(self.results)

    @computed_field
    @property
    def dimension_pass_rates(self) -> Dict[str, float]:
        """Pass rate for each dimension."""
        if not self.results:
            return {}

        dimensions = [
            'factual_accuracy', 'curriculum_alignment', 'cognitive_demand',
            'distractor_quality', 'explanation_quality', 'clarity', 'difficulty_alignment'
        ]
        rates = {}
        for dim in dimensions:
            passed = sum(1 for r in self.results.values() if getattr(r, dim).score == 1.0)
            rates[dim] = passed / len(self.results)
        return rates
