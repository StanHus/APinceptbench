# AP Benchmark Evaluation Process

## Overview

The AP Benchmark is an independent evaluation system that assesses generated AP Social Studies questions. It uses Claude API (not the same model as the generator) to ensure impartial evaluation.

## Directory Structure

```
ap_benchmark/
├── docs/                    # Documentation
├── core/
│   ├── evaluator.py        # Claude-based evaluation (temp=0.0)
│   ├── scorer.py           # Deterministic scoring
│   ├── models.py           # Pydantic models
│   ├── curriculum.py       # Curriculum context builder
│   └── hash.py             # Question hashing
├── prompts/
│   ├── base.py             # Master evaluation prompt
│   ├── mcq.py              # MCQ-specific criteria
│   ├── msq.py              # MSQ-specific criteria
│   ├── fill_in.py          # Fill-in-specific criteria
│   ├── match.py            # Match-specific criteria
│   └── article.py          # Article-specific criteria
├── hard_fail/
│   ├── rules.py            # Pattern-based hard fail rules
│   └── checker.py          # Pre-evaluation checks
├── calibration/
│   ├── gold_standard.json  # Known-good/bad examples
│   └── validator.py        # Evaluator accuracy checker
└── tests/
    └── test_*.py           # Unit tests
```

## Evaluation Flow

```
┌─────────────────┐
│ Input Question  │
└────────┬────────┘
         │
         ▼
┌─────────────────┐     ┌──────────────────┐
│  Hard Fail      │────▶│ HARD FAIL (0.0)  │
│  Checker        │ yes │ No API call      │
└────────┬────────┘     └──────────────────┘
         │ no
         ▼
┌─────────────────┐
│ Build Curriculum│
│ Context         │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Claude API      │
│ (temp=0.0)      │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Parse Response  │
│ Extract Scores  │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Calculate Final │
│ Score (0.0-1.0) │
└─────────────────┘
```

## Running Evaluation

### Evaluate a batch of questions:

```bash
cd /path/to/evaluator
export ANTHROPIC_API_KEY="your-key"
python -m ap_benchmark.benchmark --input questions.json
```

### Evaluate via workflow agent:

```bash
python workflow/agents/evaluate_questions.py --input path/to/generated.json
```

### Evaluate with sampling:

```bash
python workflow/agents/evaluate_questions.py --sample 50
```

## Evaluation Dimensions

### Critical Dimensions (cause immediate failure if 0.0)
- **factual_accuracy** - All facts must be correct
- **curriculum_alignment** - Must match requested standard

### Non-Critical Dimensions
- **cognitive_demand** - Must require analysis, not just recall
- **distractor_quality** - Distractors must be plausible
- **explanation_quality** - Must explain WHY answer is correct
- **clarity** - Must be unambiguous
- **difficulty_alignment** - Must match requested difficulty

## Scoring

### Binary Dimension Scores
Each dimension scores exactly **0.0** or **1.0** - no partial credit.

### Overall Score Calculation

| Critical Fails | Non-Critical Fails | Score Range |
|----------------|-------------------|-------------|
| 0              | 0                 | 0.95-1.00   |
| 0              | 1                 | 0.85-0.89   |
| 0              | 2+                | 0.75-0.84   |
| 1              | any               | 0.40-0.69   |
| 2              | any               | 0.00-0.39   |

### Pass Threshold: **0.85**

## Hard Fail Rules

Hard fails trigger BEFORE the API call, saving time and money.

| Rule | Applies To | Description |
|------|------------|-------------|
| `missing_explanation` | All | No explanation provided |
| `explanation_too_short` | All | Explanation < 50 chars |
| `absolute_language_in_distractors` | MCQ, MSQ | Contains "total", "never", "always" |
| `recall_only_question` | All | "What year...", "Who was..." |
| `giveaway_answer_option` | MCQ, MSQ | "All of the above" |
| `mcq_wrong_option_count` | MCQ | Not exactly 4 options |
| `msq_wrong_option_count` | MSQ | Not exactly 5 options |
| `msq_wrong_correct_count` | MSQ | Not 2-3 correct answers |

## Output Files

Evaluation results are saved to:

```
workflow/reports/
├── evaluation_YYYYMMDD_HHMMSS.json   # Detailed results
├── REPORT_YYYYMMDD_HHMMSS.md         # Human-readable report
├── history.json                       # Pass rates over time
├── issue_tracker.json                 # Issue tracking across iterations
└── monitor_YYYYMMDD_HHMMSS.json      # Evaluator health report
```

## Independence Principle

The evaluator is INDEPENDENT from the generator:
- Generator uses Gemini API
- Evaluator uses Claude API
- Evaluator criteria should NOT be influenced by generator output
- Changes to evaluator based on benchmark accuracy, not pass rate
