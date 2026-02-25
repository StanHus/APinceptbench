# AP Benchmark

Independent, deterministic benchmark system for evaluating AP Social Studies questions using Claude as an evaluator.

## Features

- **Request-Centric Evaluation**: Questions are evaluated against the original generation request, not in isolation
- **Dynamic Curriculum Context**: Follows InceptBench methodology with confidence levels (GUARANTEED/HARD/SOFT)
- **Binary Scoring**: No partial credit - each dimension scores 0.0 (fail) or 1.0 (pass)
- **Deterministic Results**: Uses temperature=0.0 for reproducible evaluations
- **Hard Fail Rules**: Pre-evaluation checks reject obviously bad questions before API calls
- **Image Support**: Evaluates questions with images using Claude's vision capabilities

## Installation

```bash
pip install -e .
```

## Usage

### CLI

```bash
# Evaluate questions from a JSON file
ap-benchmark --input questions.json

# Run calibration to verify evaluator accuracy
ap-benchmark --calibrate

# Output as markdown report
ap-benchmark --input questions.json --format markdown
```

### Python API

```python
from ap_benchmark import evaluate_question, evaluate_with_request, EvaluationRequest

# Evaluate with explicit request (recommended)
request = EvaluationRequest(
    substandard_id="AP.USH.3.1",
    substandard_description="Explain causes of the American Revolution",
    difficulty="medium",
    question_type="mcq",
    lesson_title="Road to Independence",
)

result = evaluate_question(question_dict, request=request)
print(f"Passed: {result.passed}")
print(f"Score: {result.overall_score}")

# Or evaluate with request dict
result = evaluate_with_request(question_dict, request_dict)
```

## Scoring System

### Dimensions

| Dimension | Type | Description |
|-----------|------|-------------|
| `factual_accuracy` | Critical | All facts, dates, names must be correct |
| `curriculum_alignment` | Critical | Content must match requested standard |
| `cognitive_demand` | Non-critical | Must require analysis, not just recall |
| `distractor_quality` | Non-critical | Wrong answers must be plausible |
| `explanation_quality` | Non-critical | Must explain why answer is correct |
| `clarity` | Non-critical | Must be clear and unambiguous |
| `difficulty_alignment` | Non-critical | Must match requested difficulty |

### Overall Score Calculation

| Critical Fails | Non-Critical Fails | Score Range | Result |
|----------------|-------------------|-------------|--------|
| 0 | 0 | 0.95-1.00 | PASS |
| 0 | 1 | 0.85-0.89 | PASS |
| 0 | 2+ | 0.75-0.84 | FAIL |
| 1 | any | 0.60-0.69 | FAIL |
| 2 | any | 0.30-0.39 | FAIL |

**Pass Threshold: 0.85** (fixed, never changes)

## Confidence Levels

Following InceptBench methodology:

- **GUARANTEED**: Explicit `substandard_id` provided - strictest evaluation
- **HARD**: Generation instructions or description provided - strict evaluation
- **SOFT**: Content inference only - conservative evaluation

## Hard Fail Rules

Questions are automatically rejected (score=0.0) without API call if:

- **Absolute language** in distractors: "total", "complete", "immediate", "all", "never"
- **Recall-only** questions: "What year...", "Who was..."
- **MSQ structure** violations: Not 5 options or not 2-3 correct answers
- **Missing explanation**: No or minimal explanation provided
- **Giveaway answers**: Correct answer contains "correctly states", "accurately describes"

## Environment Variables

```bash
ANTHROPIC_API_KEY=your-api-key  # Required for evaluation
```

## Development

```bash
# Install with dev dependencies
pip install -e ".[dev]"

# Run tests
pytest ap_benchmark/tests/ -v

# Run calibration
python -m ap_benchmark --calibrate
```

## Project Structure

```
ap_benchmark/
├── __init__.py          # Package exports
├── __main__.py          # Module runner
├── benchmark.py         # CLI entry point
├── core/
│   ├── models.py        # Pydantic models (BenchmarkResult, etc.)
│   ├── evaluator.py     # Claude-based evaluation
│   ├── scorer.py        # Deterministic scoring
│   ├── curriculum.py    # Dynamic curriculum context
│   └── hash.py          # Question hashing
├── prompts/
│   ├── base.py          # Master evaluation prompt
│   ├── mcq.py           # MCQ-specific criteria
│   ├── msq.py           # MSQ-specific criteria
│   ├── fill_in.py       # Fill-in-specific criteria
│   ├── match.py         # Match-specific criteria
│   └── article.py       # Article-specific criteria
├── hard_fail/
│   ├── rules.py         # Pattern-based rules
│   └── checker.py       # Pre-evaluation checks
├── calibration/
│   ├── gold_standard.json  # Known good/bad examples
│   └── validator.py     # Evaluator accuracy checker
└── tests/
    └── test_benchmark.py   # Unit tests
```

## License

MIT
