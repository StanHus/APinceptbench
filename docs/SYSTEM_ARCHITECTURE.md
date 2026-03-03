# AP Question Evaluator - System Architecture

> **Version:** 2.0.0 | **Last Updated:** 2026-03-03
> **Grade:** AP (Advanced Placement)
> **Subjects:** APUSH, APWH
> **Question Types:** MCQ, MCQ_SET, SAQ, LEQ, DBQ

---

## ⚠️ Integration Requirements

> **READ FIRST** - Critical instructions for the integration team.

### 1. This Is NOT a Standalone Repository

This evaluator will be **merged into the monolithic evaluator codebase**, not linked as a submodule or separate repo.

- Clone this repo temporarily for integration
- Copy the relevant code into the monolith's architecture
- Delete the cloned repo after integration
- **Do not maintain this as a separate GitHub dependency**

### 2. Database Integration Must Be Swappable

The current implementation uses MongoDB (`ap_social_studies` database). This must be preserved initially but designed for clean migration:

**Current Setup:**
```python
# evaluation_server.py
MONGODB_URI = os.environ.get('MONGODB_URI')
client = MongoClient(MONGODB_URI)
db = client['ap_social_studies']
```

**Integration Requirement:**
- Keep the current MongoDB connection working for initial deployment
- Abstract database access behind an interface/adapter pattern
- When the evaluator team migrates data to the central DB, swap the adapter
- Key collections to migrate: `facts` (curriculum), `benchmark_evaluations`, `benchmark_runs`

**Suggested Abstraction:**
```python
# Create a data access layer that can be swapped
class CurriculumRepository:
    def get_random_standard(self, course: str = None) -> dict: ...
    def get_standard_by_id(self, node_id: str) -> dict: ...

class EvaluationRepository:
    def save_evaluation(self, result: dict) -> str: ...
    def get_evaluation(self, eval_id: str) -> dict: ...

# Current implementation
class MongoCurriculumRepository(CurriculumRepository): ...

# Future implementation (when migrated)
class CentralDBCurriculumRepository(CurriculumRepository): ...
```

### 3. Integration Workflow

```
1. Clone this repo locally (temporary)
2. Review SYSTEM_ARCHITECTURE.md (this file)
3. Identify target location in monolith
4. Copy code files:
   - ap_benchmark/prompts/ → [monolith]/evaluators/ap/prompts/
   - evaluation_server.py → adapt to monolith's API framework
   - data/*.json → import into central DB or keep as fallback
5. Adapt imports and configurations
6. Create PR against monolith
7. Delete the cloned repo
8. Do NOT maintain as separate dependency
```

### 4. Files to Integrate

| Source | Priority | Notes |
|--------|----------|-------|
| `ap_benchmark/prompts/official_ap_prompts.py` | **Critical** | Evaluation rubrics - core logic |
| `ap_benchmark/prompts/official_ap_formatters.py` | **Critical** | Question formatters |
| `evaluation_server.py` | High | Adapt to monolith's API framework |
| `data/curriculum_facts.json` | High | Import to central DB |
| `data/curriculum_relationships.json` | Medium | Import if relationships needed |
| `test_server.py` | Medium | Adapt tests to monolith's test framework |

---

## Table of Contents

1. [Quick Start](#1-quick-start)
2. [System Overview](#2-system-overview)
3. [Data Layer](#3-data-layer)
4. [Curriculum Schema](#4-curriculum-schema)
5. [Evaluation Engine](#5-evaluation-engine)
6. [API Reference](#6-api-reference)
7. [Code Examples](#7-code-examples)
8. [Integration Patterns](#8-integration-patterns)
9. [File Reference](#9-file-reference)

---

## 1. Quick Start

### Dependencies

```bash
pip install anthropic flask flask-cors pymongo python-dotenv
```

### Environment Variables

```bash
# .env file
MONGODB_URI=mongodb+srv://user:pass@cluster.mongodb.net/
ANTHROPIC_API_KEY=sk-ant-api03-...
```

### Run Server

```bash
python evaluation_server.py
# Server starts at http://0.0.0.0:8080
```

### Test

```bash
curl http://localhost:8080/health
# {"status": "healthy", "api_version": "2.0.0"}
```

---

## 2. System Overview

```
┌─────────────────────────────────────────────────────────────────────────┐
│                              GENERATOR                                   │
│                     (Your question generation system)                    │
│                                                                          │
│   1. GET /get_standard ─────────────────────────────────┐               │
│      - Receives curriculum fact                          │               │
│      - Generates question                                │               │
│                                                          ▼               │
│   2. POST /evaluate ◄─────────────────────────── Generated Question     │
│      - Sends question + original standard                                │
│      - Receives pass/fail + detailed feedback                           │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                         EVALUATION SERVER                                │
│                       (evaluation_server.py)                             │
│                                                                          │
│  ┌────────────────┐  ┌────────────────┐  ┌────────────────────────┐    │
│  │ /get_standard  │  │   /evaluate    │  │    /evaluate_batch     │    │
│  │                │  │                │  │                        │    │
│  │ Returns random │  │ Validates &    │  │ Batch processing       │    │
│  │ curriculum     │  │ scores question│  │ multiple questions     │    │
│  │ standard       │  │ via Claude API │  │                        │    │
│  └───────┬────────┘  └───────┬────────┘  └────────────────────────┘    │
│          │                   │                                          │
│          │                   ▼                                          │
│          │    ┌──────────────────────────────────────────────────┐     │
│          │    │              EVALUATION ENGINE                    │     │
│          │    │                                                   │     │
│          │    │  official_ap_prompts.py   ← Rubric prompts       │     │
│          │    │  official_ap_formatters.py ← Format questions    │     │
│          │    │  Claude API (Anthropic)   ← LLM evaluation       │     │
│          │    │                                                   │     │
│          │    │  Pass/Fail Logic:                                │     │
│          │    │  - Hard-fail dimensions must be 1.0              │     │
│          │    │  - Overall score must be >= 0.70                 │     │
│          │    └──────────────────────────────────────────────────┘     │
│          │                                                              │
└──────────┼──────────────────────────────────────────────────────────────┘
           │
           ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                            DATA LAYER                                    │
│                     MongoDB: ap_social_studies                           │
│                                                                          │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────────┐     │
│  │     facts       │  │  relationships  │  │    embeddings       │     │
│  │   (3,347 docs)  │  │  (2,375 docs)   │  │   (3,301 docs)      │     │
│  │                 │  │                 │  │                     │     │
│  │ Curriculum      │  │ Node            │  │ Vector search       │     │
│  │ standards       │  │ connections     │  │ (optional)          │     │
│  └─────────────────┘  └─────────────────┘  └─────────────────────┘     │
│                                                                          │
│  Also available as JSON exports:                                         │
│  - data/curriculum_facts.json                                            │
│  - data/curriculum_relationships.json                                    │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## 3. Data Layer

### MongoDB Collections

| Collection | Count | Purpose | Required |
|------------|-------|---------|----------|
| `facts` | 3,347 | Curriculum standards | **Yes** |
| `relationships` | 2,375 | Node connections | No |
| `embeddings` | 3,301 | Vector search | No |
| `benchmark_runs` | 25+ | Run metadata | No |
| `benchmark_evaluations` | 3,021+ | Evaluation results | No |

### Alternative: JSON Files

If you prefer not to use MongoDB, curriculum data is exported to:

```
data/
├── curriculum_facts.json         # 3,347 curriculum standards
└── curriculum_relationships.json # 2,375 relationships
```

Load directly:

```python
import json

with open('data/curriculum_facts.json') as f:
    curriculum = json.load(f)

# Filter by course
apush_facts = [f for f in curriculum if f['course'] == 'APUSH']
apwh_facts = [f for f in curriculum if f['course'] == 'APWH']
```

---

## 4. Curriculum Schema

### Fact Document Structure

```json
{
  "node_id": "KC-1.1.I.A",
  "course": "APUSH",
  "unit": 1,
  "topic": "Native American Societies Before European Contact",
  "cluster": "Native American Societies Before European Contact",
  "classification": "essential",

  "learning_objective": "Explain how and why various native populations in the period before European contact interacted with the natural environment in North America",

  "historical_development": "The spread of maize cultivation from present day Mexico northward into the present-day American Southwest and beyond supported economic development, settlement, advanced irrigation, and social diversification among societies.",

  "date": "2500 BCE - 1500 CE",
  "theme": "GEO",

  "confidence": 1.0,
  "is_definition": false,
  "source_file": "AP US History - Knowledge Schema.xlsx",
  "loaded_at": "2026-02-17T14:31:16"
}
```

### Field Reference

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `node_id` | string | **Yes** | Unique identifier (e.g., "KC-1.1.I.A") |
| `course` | string | **Yes** | "APUSH" or "APWH" |
| `unit` | int | **Yes** | Unit number 1-9 |
| `topic` | string | **Yes** | Topic name |
| `learning_objective` | string | **Yes** | What students should learn |
| `historical_development` | string | **Yes** | The curriculum fact/content |
| `date` / `time_period` | string | **Yes** | Historical time period |
| `theme` | string | No | AP Theme code (GEO, WXT, MIG, etc.) |
| `classification` | string | No | essential, important, supplementary |
| `cluster` | string | No | Grouping cluster |

### Curriculum Coverage

| Course | Facts | Units | Topics |
|--------|-------|-------|--------|
| APUSH | 1,757 | 1-9 | American History 1491-Present |
| APWH | 1,590 | 1-9 | World History 1200-Present |
| **Total** | **3,347** | | |

---

## 5. Evaluation Engine

### Components

#### 5.1 Evaluation Prompts (`ap_benchmark/prompts/official_ap_prompts.py`)

Contains LLM prompts that encode AP rubric criteria:

```python
MCQ_EVALUATION_PROMPT = """
You are an expert AP History question evaluator...

EVALUATION DIMENSIONS:
1. factual_accuracy - Are all facts historically correct?
2. answer_validity - Is there exactly ONE defensible correct answer?
3. stimulus_alignment - Does the question require the stimulus?
4. distractor_quality - Are wrong answers plausible but clearly wrong?
5. skill_alignment - Does it test AP historical thinking skills?
6. clarity - Is wording clear and unambiguous?

For each dimension, provide:
- score: 0.0 to 1.0
- reasoning: explanation
- issues: list of specific problems

Return as JSON...
"""
```

**Available Prompts:**
- `MCQ_EVALUATION_PROMPT`
- `MCQ_SET_EVALUATION_PROMPT`
- `SAQ_EVALUATION_PROMPT`
- `LEQ_EVALUATION_PROMPT`
- `DBQ_EVALUATION_PROMPT`
- `PROMPT_VERSION` (version string)

#### 5.2 Question Formatters (`ap_benchmark/prompts/official_ap_formatters.py`)

Converts various input formats into standardized text for evaluation:

```python
from ap_benchmark.prompts.official_ap_formatters import format_question_content

formatted = format_question_content(
    question_type="mcq",
    question_data={
        "stimulus": "The cotton gin made cotton production highly profitable...",
        "stem": "The development described most directly contributed to which of the following?",
        "choices": {
            "A": "The expansion of plantation agriculture",
            "B": "The decline of the Atlantic slave trade",
            "C": "The rise of industrial manufacturing",
            "D": "The gradual emancipation of enslaved people"
        },
        "correct_answer": "A",
        "explanation": "The cotton gin increased profitability..."
    },
    context={
        "course": "APUSH",
        "topic": "Cotton and Slavery",
        "learning_objective": "Explain the causes of slavery expansion..."
    }
)
```

**Supported Input Formats:**

MCQ choices can be either:
```python
# Format 1: Dict
{"A": "text", "B": "text", "C": "text", "D": "text"}

# Format 2: Array
[{"key": "A", "text": "..."}, {"key": "B", "text": "..."}, ...]
```

SAQ parts can be either:
```python
# Format 1: Dict
{"a": {"prompt": "..."}, "b": {"prompt": "..."}, "c": {"prompt": "..."}}

# Format 2: Array
[{"part": "a", "prompt": "..."}, ...]
```

#### 5.3 Pass/Fail Logic

```python
# Hard-fail dimensions - ANY score < 1.0 causes automatic FAIL
HARD_FAIL_DIMENSIONS = {
    "document_count",      # DBQ: correct number of documents
    "prompt_structure",    # LEQ/DBQ/SAQ: valid prompt format
    "factual_accuracy",    # All: no historical errors
    "answer_validity",     # MCQ: exactly one correct answer
}

# Pass criteria
def check_pass(dimensions, overall_score):
    # Check hard-fail dimensions
    for dim in HARD_FAIL_DIMENSIONS:
        if dim in dimensions:
            if dimensions[dim]["score"] < 1.0:
                return False, f"Hard-fail: {dim}"

    # Check overall threshold
    if overall_score < 0.70:
        return False, f"Score {overall_score} below 0.70 threshold"

    return True, "Passed"
```

---

## 6. API Reference

### GET /get_standard

Get a random curriculum standard for question generation.

```bash
curl "http://localhost:8080/get_standard?course=APUSH"
```

**Query Parameters:**
| Param | Required | Values | Default |
|-------|----------|--------|---------|
| `course` | No | APUSH, APWH | Random |

**Response:**
```json
{
  "success": true,
  "standard": {
    "node_id": "KC-1.1.I.A",
    "course": "APUSH",
    "unit": 1,
    "topic": "Native American Societies Before European Contact",
    "learning_objective": "Explain how and why...",
    "curriculum_fact": "The spread of maize cultivation...",
    "time_period": "2500 BCE - 1500 CE",
    "theme": "GEO"
  },
  "_usage": "Pass this 'standard' object as 'request' field when calling POST /evaluate"
}
```

### POST /evaluate

Evaluate a generated question.

```bash
curl -X POST "http://localhost:8080/evaluate" \
  -H "Content-Type: application/json" \
  -d '{
    "type": "mcq",
    "difficulty": "medium",
    "request": {
      "node_id": "KC-1.1.I.A",
      "course": "APUSH",
      "unit": 1,
      "topic": "Native American Societies",
      "learning_objective": "Explain how and why...",
      "curriculum_fact": "The spread of maize...",
      "time_period": "2500 BCE - 1500 CE",
      "theme": "GEO"
    },
    "output": {
      "stimulus": "Archaeological evidence shows...",
      "stem": "The developments described most directly resulted from which of the following?",
      "choices": {
        "A": "The spread of agricultural practices from Mesoamerica",
        "B": "Trade networks with European explorers",
        "C": "Climate change in the Southwest",
        "D": "Migration from Asia across the Bering Strait"
      },
      "correct_answer": "A",
      "explanation": "Maize cultivation spread northward..."
    }
  }'
```

**Response:**
```json
{
  "success": true,
  "passed": true,
  "overall_score": 0.917,
  "critical_failed": false,
  "failed_hard_dimensions": [],
  "dimensions": {
    "factual_accuracy": {
      "score": 1.0,
      "reasoning": "All historical facts are accurate...",
      "issues": []
    },
    "answer_validity": {
      "score": 1.0,
      "reasoning": "Option A is clearly the best answer...",
      "issues": []
    },
    "stimulus_alignment": {
      "score": 0.75,
      "reasoning": "Question requires stimulus but...",
      "issues": ["Minor: stimulus could be more integral"]
    },
    "distractor_quality": {
      "score": 0.75,
      "reasoning": "Most distractors are plausible...",
      "issues": ["Option B is anachronistic"]
    },
    "skill_alignment": {
      "score": 1.0,
      "reasoning": "Tests causation skill appropriately...",
      "issues": []
    },
    "clarity": {
      "score": 1.0,
      "reasoning": "Clear and unambiguous wording...",
      "issues": []
    }
  },
  "issues": [
    {
      "dimension": "stimulus_alignment",
      "severity": "minor",
      "explanation": "The stimulus could be more integral..."
    }
  ],
  "overall_assessment": "PASS. Question meets AP standards...",
  "evaluator_version": "2026.02.24.2",
  "evaluated_at": "2026-03-03T09:30:00Z"
}
```

---

## 7. Code Examples

### 7.1 Standalone Evaluation (No Server)

```python
import json
import anthropic
from ap_benchmark.prompts.official_ap_prompts import (
    MCQ_EVALUATION_PROMPT,
    MCQ_SET_EVALUATION_PROMPT,
    SAQ_EVALUATION_PROMPT,
    LEQ_EVALUATION_PROMPT,
    DBQ_EVALUATION_PROMPT,
)
from ap_benchmark.prompts.official_ap_formatters import format_question_content

# Initialize Anthropic client
client = anthropic.Anthropic()

def evaluate_question(question_type: str, question_data: dict, curriculum_context: dict) -> dict:
    """
    Evaluate a question without using the API server.

    Args:
        question_type: mcq, mcq_set, saq, leq, dbq
        question_data: Generated question content
        curriculum_context: Original curriculum standard

    Returns:
        Evaluation result dict with pass/fail and scores
    """

    # 1. Select appropriate prompt
    prompts = {
        'mcq': MCQ_EVALUATION_PROMPT,
        'mcq_set': MCQ_SET_EVALUATION_PROMPT,
        'saq': SAQ_EVALUATION_PROMPT,
        'leq': LEQ_EVALUATION_PROMPT,
        'dbq': DBQ_EVALUATION_PROMPT,
    }
    base_prompt = prompts[question_type]

    # 2. Format the question
    formatted_question = format_question_content(
        question_type=question_type,
        question_data=question_data,
        context=curriculum_context
    )

    # 3. Combine prompt with question
    full_prompt = f"{base_prompt}\n\n---\n\nQUESTION TO EVALUATE:\n\n{formatted_question}"

    # 4. Call Claude API
    response = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=4096,
        messages=[{"role": "user", "content": full_prompt}]
    )

    # 5. Parse response
    text = response.content[0].text
    if "```json" in text:
        json_str = text.split("```json")[1].split("```")[0]
    elif "```" in text:
        json_str = text.split("```")[1].split("```")[0]
    else:
        json_str = text

    result = json.loads(json_str.strip())

    # 6. Calculate overall score
    dimensions = result.get("dimensions", {})
    scores = [d.get("score", 0) for d in dimensions.values() if isinstance(d, dict)]
    overall_score = sum(scores) / len(scores) if scores else 0

    # 7. Check hard-fail dimensions
    hard_fail_dims = {"document_count", "prompt_structure", "factual_accuracy", "answer_validity"}
    critical_failed = False
    failed_dims = []

    for dim in hard_fail_dims:
        if dim in dimensions:
            score = dimensions[dim].get("score", 1.0)
            if score < 1.0:
                critical_failed = True
                failed_dims.append(dim)

    # 8. Determine pass/fail
    passed = not critical_failed and overall_score >= 0.70

    return {
        "passed": passed,
        "overall_score": round(overall_score, 3),
        "critical_failed": critical_failed,
        "failed_hard_dimensions": failed_dims,
        "dimensions": dimensions,
        "issues": result.get("issues", []),
        "overall_assessment": result.get("overall_assessment", "")
    }


# Example usage
if __name__ == "__main__":
    result = evaluate_question(
        question_type="mcq",
        question_data={
            "stimulus": "The cotton gin made cotton production highly profitable...",
            "stem": "The development described most directly contributed to which?",
            "choices": {
                "A": "Expansion of plantation agriculture",
                "B": "Decline of the Atlantic slave trade",
                "C": "Rise of industrial manufacturing in the South",
                "D": "Gradual emancipation of enslaved people"
            },
            "correct_answer": "A",
            "explanation": "The cotton gin increased profitability..."
        },
        curriculum_context={
            "course": "APUSH",
            "topic": "Cotton and the Expansion of Slavery",
            "learning_objective": "Explain causes of slavery expansion...",
            "time_period": "1800-1848"
        }
    )

    print(f"Passed: {result['passed']}")
    print(f"Score: {result['overall_score']}")
```

### 7.2 Using the API Server

```python
import requests

BASE_URL = "http://localhost:8080"

def get_standard(course: str = None) -> dict:
    """Get a curriculum standard for question generation."""
    params = {"course": course} if course else {}
    response = requests.get(f"{BASE_URL}/get_standard", params=params)
    return response.json()

def evaluate_question(question_type: str, difficulty: str,
                      standard: dict, output: dict) -> dict:
    """Evaluate a generated question."""
    payload = {
        "type": question_type,
        "difficulty": difficulty,
        "request": standard,  # Pass the standard from get_standard
        "output": output
    }
    response = requests.post(f"{BASE_URL}/evaluate", json=payload)
    return response.json()

# Example workflow
standard = get_standard(course="APUSH")["standard"]
print(f"Got standard: {standard['topic']}")

# ... your generator creates a question ...

result = evaluate_question(
    question_type="mcq",
    difficulty="medium",
    standard=standard,
    output={
        "stimulus": "...",
        "stem": "...",
        "choices": {"A": "...", "B": "...", "C": "...", "D": "..."},
        "correct_answer": "A",
        "explanation": "..."
    }
)

if result["passed"]:
    print(f"✅ Passed with score {result['overall_score']}")
else:
    print(f"❌ Failed: {result['failed_hard_dimensions']}")
    for issue in result["issues"]:
        print(f"  - {issue['dimension']}: {issue['explanation']}")
```

### 7.3 Loading Curriculum from JSON

```python
import json
import random

# Load curriculum
with open('data/curriculum_facts.json') as f:
    curriculum = json.load(f)

# Filter by course
apush = [f for f in curriculum if f['course'] == 'APUSH']
apwh = [f for f in curriculum if f['course'] == 'APWH']

# Get by unit
unit_3_apush = [f for f in apush if f.get('unit') == 3]

# Random standard
standard = random.choice(curriculum)

# Search by topic
slavery_facts = [
    f for f in curriculum
    if 'slavery' in f.get('topic', '').lower()
    or 'slavery' in f.get('historical_development', '').lower()
]

# Convert to the format expected by /evaluate
def fact_to_request(fact: dict) -> dict:
    return {
        "node_id": fact.get("node_id"),
        "course": fact.get("course"),
        "unit": fact.get("unit"),
        "topic": fact.get("topic"),
        "learning_objective": fact.get("learning_objective", ""),
        "curriculum_fact": fact.get("historical_development", ""),
        "time_period": fact.get("date", fact.get("time_period", "")),
        "theme": fact.get("theme", "")
    }

request = fact_to_request(standard)
```

### 7.4 Batch Evaluation

```python
import concurrent.futures
import requests

def evaluate_batch(questions: list, max_workers: int = 5) -> list:
    """Evaluate multiple questions concurrently."""

    def eval_one(q):
        return requests.post(
            "http://localhost:8080/evaluate",
            json=q
        ).json()

    results = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = [executor.submit(eval_one, q) for q in questions]
        for future in concurrent.futures.as_completed(futures):
            results.append(future.result())

    return results

# Calculate pass rate
def calculate_stats(results: list) -> dict:
    passed = sum(1 for r in results if r.get("passed"))
    failed = len(results) - passed
    return {
        "total": len(results),
        "passed": passed,
        "failed": failed,
        "pass_rate": passed / len(results) if results else 0
    }
```

---

## 8. Integration Patterns

### Pattern A: API Server (Recommended)

Run `evaluation_server.py` as a standalone service. Generators call the API endpoints.

```
[Generator] ──HTTP──▶ [Evaluation Server] ──▶ [Claude API]
                              │
                              ▼
                         [MongoDB]
```

**Pros:** Decoupled, can scale independently, easy to monitor
**Cons:** Network latency, requires running server

### Pattern B: Direct Import

Import evaluation functions directly into your codebase.

```python
# Copy ap_benchmark/prompts/ to your repo
from ap_benchmark.prompts.official_ap_prompts import MCQ_EVALUATION_PROMPT
from ap_benchmark.prompts.official_ap_formatters import format_question_content
```

**Pros:** No network calls, simpler deployment
**Cons:** Tightly coupled, need to copy files

### Pattern C: Hybrid

Use JSON exports for curriculum, API for evaluation.

```python
# Load curriculum from JSON (no MongoDB needed)
with open('curriculum_facts.json') as f:
    curriculum = json.load(f)

# Call evaluation API
result = requests.post("http://eval-server/evaluate", json={...})
```

---

## 9. File Reference

```
evaluator/
│
├── evaluation_server.py           # Main API server (32KB)
│   - Flask application
│   - All API endpoints
│   - Validation logic
│   - Pass/fail determination
│
├── .env                           # Environment variables
│   - MONGODB_URI
│   - ANTHROPIC_API_KEY
│
├── ap_benchmark/
│   └── prompts/
│       ├── __init__.py
│       ├── official_ap_prompts.py    # Evaluation prompts (26KB)
│       │   - MCQ_EVALUATION_PROMPT
│       │   - MCQ_SET_EVALUATION_PROMPT
│       │   - SAQ_EVALUATION_PROMPT
│       │   - LEQ_EVALUATION_PROMPT
│       │   - DBQ_EVALUATION_PROMPT
│       │   - PROMPT_VERSION
│       │
│       └── official_ap_formatters.py # Question formatters (31KB)
│           - format_question_content()
│           - format_mcq()
│           - format_mcq_set()
│           - format_saq()
│           - format_leq()
│           - format_dbq()
│
├── data/
│   ├── curriculum_facts.json         # Exported curriculum (3,347 facts)
│   └── curriculum_relationships.json # Exported relationships
│
├── docs/
│   ├── README.md                     # Documentation index
│   ├── SYSTEM_ARCHITECTURE.md        # This file
│   ├── EVALUATION_API.md             # API reference (24KB)
│   ├── EVALUATION_PROCESS.md         # Evaluation details
│   ├── AP_QUESTION_TYPES_SPEC.md     # Question type specs
│   └── reports/                      # Historical benchmark reports
│
├── benchmark_official.py             # Batch benchmark runner
├── generate_detailed_report.py       # Report generation
└── test_server.py                    # Server test suite
```

---

## Appendix: Question Type Output Schemas

### MCQ

```json
{
  "stimulus": "Primary source text or context...",
  "stem": "The question being asked?",
  "choices": {
    "A": "First option",
    "B": "Second option",
    "C": "Third option",
    "D": "Fourth option"
  },
  "correct_answer": "A",
  "explanation": "Why A is correct..."
}
```

### MCQ_SET

```json
{
  "stimulus": "Shared stimulus for all questions...",
  "questions": [
    {
      "stem": "First question?",
      "choices": {"A": "...", "B": "...", "C": "...", "D": "..."},
      "correct_answer": "B",
      "explanation": "..."
    },
    {
      "stem": "Second question?",
      "choices": {"A": "...", "B": "...", "C": "...", "D": "..."},
      "correct_answer": "A",
      "explanation": "..."
    }
  ]
}
```

### SAQ

```json
{
  "stimulus": "Primary source or context...",
  "parts": {
    "a": {
      "prompt": "Part A question...",
      "scoring_notes": "What a good answer includes..."
    },
    "b": {
      "prompt": "Part B question...",
      "scoring_notes": "..."
    },
    "c": {
      "prompt": "Part C question...",
      "scoring_notes": "..."
    }
  }
}
```

### LEQ

```json
{
  "prompt": "Evaluate the extent to which...",
  "time_period": "1800-1848",
  "reasoning_type": "causation",
  "scoring_guidance": {
    "thesis_examples": ["Example thesis 1", "Example thesis 2"],
    "contextualization_notes": ["Context point 1", "Context point 2"],
    "evidence_expectations": ["Evidence 1", "Evidence 2"]
  }
}
```

### DBQ

```json
{
  "prompt": "Evaluate the extent to which...",
  "documents": [
    {
      "number": 1,
      "source": "Author, Title, Date",
      "content": "Document text..."
    }
  ],
  "time_period": "1800-1848",
  "scoring_guidance": {
    "thesis_examples": ["..."],
    "document_analysis_notes": ["..."],
    "outside_evidence_expectations": ["..."]
  }
}
```
