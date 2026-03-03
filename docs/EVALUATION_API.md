# AP Question Evaluation API

**Version:** 2.0.0
**Evaluator Version:** 2026.02.24.2
**Base URL:** `http://192.168.1.27:8080`

---

## Overview

This API provides curriculum standards for AP question generation and evaluates generated questions against official College Board AP rubrics.

### Workflow

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│  GET            │     │  YOUR           │     │  POST           │
│  /get_standard  │────▶│  GENERATOR      │────▶│  /evaluate      │
│                 │     │                 │     │                 │
│  Returns:       │     │  Input:         │     │  Input:         │
│  • standard     │     │  • standard     │     │  • type         │
│                 │     │  • type         │     │  • difficulty   │
│                 │     │  • difficulty   │     │  • request      │
│                 │     │                 │     │  • output       │
│                 │     │  Output:        │     │                 │
│                 │     │  • question     │     │  Returns:       │
│                 │     │                 │     │  • passed       │
│                 │     │                 │     │  • score        │
│                 │     │                 │     │  • issues       │
└─────────────────┘     └─────────────────┘     └─────────────────┘
```

**CRITICAL:** The `standard` object returned by `/get_standard` MUST be passed unchanged as the `request` field to `/evaluate`.

---

## Endpoints

### `GET /`

Returns this documentation in markdown format.

```bash
curl http://192.168.1.27:8080/
```

For JSON summary:
```bash
curl -H "Accept: application/json" http://192.168.1.27:8080/
```

---

### `GET /health`

Health check endpoint.

**Response:**
```json
{
  "status": "healthy",
  "api_version": "2.0.0",
  "evaluator_version": "2026.02.24.2",
  "timestamp": "2026-02-26T15:00:00+00:00"
}
```

---

### `GET /get_standard`

Get a random curriculum standard for question generation.

**Query Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `course` | string | No | Filter by course: `APUSH` or `APWH` |
| `unit` | integer | No | Filter by unit number (1-9) |

**Example Requests:**
```bash
# Get any random standard
curl http://192.168.1.27:8080/get_standard

# Get APUSH standard only
curl "http://192.168.1.27:8080/get_standard?course=APUSH"

# Get APUSH Unit 4 standard
curl "http://192.168.1.27:8080/get_standard?course=APUSH&unit=4"
```

**Response:**
```json
{
  "success": true,
  "standard": {
    "node_id": "KC-4.1.II.A",
    "course": "APUSH",
    "unit": 4,
    "topic": "The Rise of Political Parties and the Era of Jefferson",
    "learning_objective": "Explain how and why political ideas, institutions, and party systems developed and changed in the new republic.",
    "curriculum_fact": "The American two-party system emerged from the debates over the ratification of the Constitution and later from debates over the direction of the new nation.",
    "time_period": "1787-1820",
    "theme": "PCE"
  },
  "_usage": "Pass this 'standard' object as 'request' field when calling POST /evaluate"
}
```

**Standard Fields:**

| Field | Type | Description |
|-------|------|-------------|
| `node_id` | string | Unique curriculum node identifier (e.g., `KC-4.1.II.A`) |
| `course` | string | AP course: `APUSH` or `APWH` |
| `unit` | integer | Unit number (1-9) |
| `topic` | string | Topic/cluster name from curriculum |
| `learning_objective` | string | The AP learning objective text |
| `curriculum_fact` | string | The specific curriculum fact/statement to base question on |
| `time_period` | string | Historical time period (e.g., `1787-1820`) |
| `theme` | string | AP thematic category (see Themes below) |

**Themes:**
- `GEO` - Geography & Environment
- `WOR` - America & the World / World Interactions
- `PCE` - Politics & Power / Governance
- `CUL` - American & National Identity / Culture
- `SOC` - Social Structures
- `MIG` - Migration & Settlement
- `WXT` - Work, Exchange, Technology / Economics

---

### `GET /get_standards`

Get multiple random curriculum standards.

**Query Parameters:**

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `count` | integer | No | 5 | Number of standards (max 50) |
| `course` | string | No | - | Filter by course |

**Example:**
```bash
curl "http://192.168.1.27:8080/get_standards?count=10&course=APWH"
```

**Response:**
```json
{
  "success": true,
  "count": 10,
  "standards": [
    { "node_id": "...", "course": "APWH", ... },
    { "node_id": "...", "course": "APWH", ... },
    ...
  ]
}
```

---

### `POST /evaluate`

Evaluate a generated AP question against official rubrics.

**CRITICAL REQUIREMENTS:**

1. ✅ The `request` field MUST contain the **EXACT** standard returned by `/get_standard`
2. ✅ The `type` field MUST be one of: `mcq`, `mcq_set`, `saq`, `leq`, `dbq`
3. ✅ The `difficulty` field MUST be one of: `easy`, `medium`, `hard`
4. ✅ The `output` field MUST contain the generated question matching the type schema

**Request Body Structure:**

```json
{
  "type": "mcq",
  "difficulty": "medium",
  "request": {
    "node_id": "KC-4.1.II.A",
    "course": "APUSH",
    "unit": 4,
    "topic": "The Rise of Political Parties",
    "learning_objective": "Explain how and why political ideas changed...",
    "curriculum_fact": "The American two-party system emerged from debates...",
    "time_period": "1787-1820",
    "theme": "PCE"
  },
  "output": {
    // Generated question content - see schemas below
  }
}
```

**Required Top-Level Fields:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `type` | string | ✅ YES | Question type: `mcq`, `mcq_set`, `saq`, `leq`, `dbq` |
| `difficulty` | string | ✅ YES | Difficulty: `easy`, `medium`, `hard` |
| `request` | object | ✅ YES | **EXACT** standard from `/get_standard` |
| `output` | object | ✅ YES | Generated question content |

**Required `request` Fields (from /get_standard):**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `request.node_id` | string | ✅ YES | Curriculum node identifier |
| `request.course` | string | ✅ YES | `APUSH` or `APWH` |
| `request.unit` | integer | ✅ YES | Unit number (1-9) |
| `request.topic` | string | ✅ YES | Topic name |
| `request.learning_objective` | string | ✅ YES | Learning objective text |
| `request.curriculum_fact` | string | ✅ YES | Curriculum fact/statement |
| `request.time_period` | string | ✅ YES | Time period |
| `request.theme` | string | ✅ YES | Theme code |

---

## Output Schemas by Question Type

### MCQ Output Schema

```json
{
  "stimulus": "Primary source excerpt or contextual paragraph (REQUIRED for medium/hard)",
  "stem": "Question text ending with a question mark?",
  "choices": {
    "A": "First answer choice",
    "B": "Second answer choice",
    "C": "Third answer choice",
    "D": "Fourth answer choice"
  },
  "correct_answer": "A",
  "explanation": "Why the correct answer is correct and distractors are wrong"
}
```

**MCQ Requirements:**
- ✅ `stem` - Required
- ✅ `choices` - Required, must have exactly A, B, C, D
- ✅ `correct_answer` - Required, must be A, B, C, or D
- ⚠️ `stimulus` - Required for medium/hard difficulty
- ⚠️ `explanation` - Recommended

---

### MCQ_SET Output Schema

```json
{
  "stimulus": "Extended primary source excerpt or document (REQUIRED)",
  "questions": [
    {
      "stem": "Question 1 text?",
      "choices": {
        "A": "...",
        "B": "...",
        "C": "...",
        "D": "..."
      },
      "correct_answer": "B",
      "explanation": "..."
    },
    {
      "stem": "Question 2 text?",
      "choices": { "A": "...", "B": "...", "C": "...", "D": "..." },
      "correct_answer": "A",
      "explanation": "..."
    },
    {
      "stem": "Question 3 text?",
      "choices": { "A": "...", "B": "...", "C": "...", "D": "..." },
      "correct_answer": "D",
      "explanation": "..."
    }
  ]
}
```

**MCQ_SET Requirements:**
- ✅ `stimulus` - Required
- ✅ `questions` - Required, must have **exactly 3** questions
- ✅ Each question must have `stem`, `choices` (A-D), `correct_answer`
- ⚠️ All questions must require analysis of the shared stimulus

---

### SAQ Output Schema

```json
{
  "stimulus": "Optional primary source, image, or data",
  "preamble": "Brief contextual framing (1-2 sentences)",
  "parts": {
    "a": {
      "prompt": "Part (a) question text",
      "skill": "identify",
      "scoring_notes": "What constitutes a complete answer"
    },
    "b": {
      "prompt": "Part (b) question text",
      "skill": "describe",
      "scoring_notes": "What constitutes a complete answer"
    },
    "c": {
      "prompt": "Part (c) question text",
      "skill": "explain",
      "scoring_notes": "What constitutes a complete answer"
    }
  }
}
```

**SAQ Requirements:**
- ✅ `parts` - Required, must have exactly `a`, `b`, `c`
- ✅ Each part must have `prompt`
- ⚠️ `preamble` - Recommended
- ⚠️ `skill` - Should be one of: `identify`, `describe`, `explain`
- ⚠️ `scoring_notes` - Recommended

**SAQ Task Verb Rules:**
- Part (a): May use `identify` (lower-order)
- Parts (b) and (c): Should use `describe` or `explain` (higher-order)
- **NEVER** use compound verbs like "identify AND describe" in a single part

---

### LEQ Output Schema

```json
{
  "prompt": "Evaluate the extent to which [topic] changed during [time period].",
  "reasoning_type": "causation",
  "time_period_explicit": "1800-1848",
  "scoring_guidance": {
    "thesis_examples": [
      "Example strong thesis 1",
      "Example strong thesis 2"
    ],
    "contextualization_notes": "What historical context is relevant",
    "evidence_expectations": "What specific evidence students might cite",
    "complexity_paths": [
      "Way to earn complexity point 1",
      "Way to earn complexity point 2"
    ]
  }
}
```

**LEQ Requirements:**
- ✅ `prompt` - Required, must contain explicit time period
- ✅ `reasoning_type` - Required, must be `causation`, `comparison`, or `ccot`
- ⚠️ `time_period_explicit` - Recommended
- ⚠️ `scoring_guidance` - Recommended

**LEQ Prompt Rules:**
- Must use standard AP phrasing: "Evaluate the extent to which..."
- Must be arguable (reasonable people could disagree)
- Time period must align with `time_period` from request

---

### DBQ Output Schema

```json
{
  "prompt": "Evaluate the extent to which [topic] changed during [time period].",
  "documents": [
    {
      "number": 1,
      "source": "Author Name, Title of Document, Date",
      "type": "letter",
      "content": "Full document text or image description",
      "historical_context": "Brief context for teacher reference",
      "sourcing_notes": "HIPP analysis opportunities"
    },
    {
      "number": 2,
      "source": "...",
      "type": "speech",
      "content": "...",
      "historical_context": "...",
      "sourcing_notes": "..."
    }
    // ... exactly 7 documents total
  ],
  "scoring_guidance": {
    "thesis_examples": ["..."],
    "document_groupings": ["Possible grouping 1", "Possible grouping 2"],
    "outside_evidence": ["Relevant outside evidence 1", "..."],
    "complexity_paths": ["..."]
  }
}
```

**DBQ Requirements:**
- ✅ `prompt` - Required
- ✅ `documents` - Required, must have **exactly 7** documents
- ✅ Each document must have `number`, `source`, `type`, `content`
- ⚠️ `historical_context` and `sourcing_notes` - Recommended

**DBQ Document Rules:**
- All documents must be authentic historical sources or clearly adapted
- Each document must have full attribution: Author, Title, Date
- Documents must span multiple perspectives/viewpoints
- Documents must be from the `time_period` specified in the request
- At least 2 different document types should be represented

**Valid Document Types:**
`letter`, `speech`, `government document`, `newspaper`, `diary`, `treaty`, `image`, `map`, `chart`, `pamphlet`, `memoir`, `petition`, `court case`, `sermon`

---

## Evaluation Response

**Success Response:**

```json
{
  "success": true,
  "passed": true,
  "overall_score": 0.917,
  "critical_failed": false,
  "failed_hard_dimensions": [],
  "dimensions": {
    "answer_validity": {
      "score": 1.0,
      "reasoning": "Exactly one unambiguously correct answer...",
      "issues": []
    },
    "clarity": {
      "score": 1.0,
      "reasoning": "Question stem is clear and unambiguous...",
      "issues": []
    },
    "distractor_quality": {
      "score": 0.75,
      "reasoning": "Three distractors are plausible but...",
      "issues": ["ISSUE1"]
    },
    "factual_accuracy": {
      "score": 1.0,
      "reasoning": "All content is historically accurate...",
      "issues": []
    },
    "skill_alignment": {
      "score": 1.0,
      "reasoning": "Tests causation skill appropriately...",
      "issues": []
    },
    "stimulus_alignment": {
      "score": 0.75,
      "reasoning": "Question requires some stimulus analysis...",
      "issues": ["ISSUE2"]
    }
  },
  "issues": [
    {
      "id": "ISSUE1",
      "dimension": "distractor_quality",
      "severity": "minor",
      "snippet": "Option C: The expansion of...",
      "explanation": "This distractor is historically implausible..."
    },
    {
      "id": "ISSUE2",
      "dimension": "stimulus_alignment",
      "severity": "minor",
      "snippet": "Which factor best explains...",
      "explanation": "Question could be answered without full stimulus analysis..."
    }
  ],
  "overall_assessment": "PASS - Well-constructed question with minor issues...",
  "evaluator_version": "2026.02.24.2",
  "evaluated_at": "2026-02-26T15:30:00+00:00",
  "request_echo": {
    "type": "mcq",
    "difficulty": "medium",
    "node_id": "KC-4.1.II.A",
    "course": "APUSH"
  }
}
```

**Error Response:**

```json
{
  "success": false,
  "error": "Missing required fields: request.curriculum_fact; Invalid type 'multiple_choice'",
  "received_fields": ["type", "output", "request.course", "request.node_id"],
  "documentation": "See GET / for full API documentation"
}
```

---

## Evaluation Dimensions by Type

### MCQ / MCQ_SET Dimensions

| Dimension | Weight | Description |
|-----------|--------|-------------|
| `answer_validity` | **HARD FAIL** | Exactly one unambiguously correct answer |
| `factual_accuracy` | **HARD FAIL** | All content historically accurate |
| `stimulus_alignment` | Normal | Question requires analysis of stimulus |
| `distractor_quality` | Normal | Wrong answers plausible but clearly inferior |
| `skill_alignment` | Normal | Tests appropriate AP skill |
| `clarity` | Normal | Clear, unambiguous wording |

### SAQ Dimensions

| Dimension | Weight | Description |
|-----------|--------|-------------|
| `prompt_structure` | **HARD FAIL** | Exactly 3 parts (a, b, c) |
| `historical_specificity` | Normal | Grounded in specific historical content |
| `answerability` | Normal | Can be answered with AP course knowledge |
| `skill_alignment` | Normal | Appropriate task verbs |
| `stimulus_integration` | Normal | Parts properly reference stimulus (if present) |
| `scoring_clarity` | Normal | Clear scoring guidance |

### LEQ Dimensions

| Dimension | Weight | Description |
|-----------|--------|-------------|
| `prompt_arguability` | Normal | Supports arguable thesis |
| `reasoning_type` | Normal | Matches requested type |
| `time_period_specificity` | Normal | Clear, appropriate time bounds |
| `evidence_accessibility` | Normal | Students can cite relevant evidence |
| `thesis_flexibility` | Normal | Multiple valid thesis approaches |
| `complexity_opportunity` | Normal | Path to earn complexity point |
| `contextualization_opportunity` | Normal | Clear contextualization opportunity |

### DBQ Dimensions

| Dimension | Weight | Description |
|-----------|--------|-------------|
| `document_count` | **HARD FAIL** | Exactly 7 documents |
| `document_authenticity` | Normal | Authentic sources with attribution |
| `document_diversity` | Normal | Multiple perspectives and types |
| `document_relevance` | Normal | All documents relevant to prompt |
| `time_period_accuracy` | Normal | Documents from correct period |
| `prompt_arguability` | Normal | Supports arguable thesis |
| `thesis_potential` | Normal | Documents support thesis development |
| `sourcing_opportunity` | Normal | Documents allow HIPP analysis |
| `outside_evidence_scope` | Normal | Clear outside evidence opportunities |

---

## Pass/Fail Criteria

A question **PASSES** if:
1. ✅ No **HARD FAIL** dimensions have score < 1.0
2. ✅ Overall score (average of all dimensions) >= 0.70

A question **FAILS** if:
- ❌ Any **HARD FAIL** dimension has score < 1.0, OR
- ❌ Overall score < 0.70

**Hard Fail Dimensions:**
- `document_count` - DBQ must have exactly 7 documents
- `prompt_structure` - SAQ must have exactly 3 parts (a, b, c)
- `factual_accuracy` - No factual errors allowed in any question type
- `answer_validity` - MCQ/MCQ_SET must have exactly 1 correct answer

---

## Complete Example

### Step 1: Get Standard

```bash
curl "http://192.168.1.27:8080/get_standard?course=APUSH&unit=4"
```

**Response:**
```json
{
  "success": true,
  "standard": {
    "node_id": "c_Ab12",
    "course": "APUSH",
    "unit": 4,
    "topic": "The Society of the South in the Early Republic",
    "learning_objective": "Explain the causes and effects of the expansion of slavery.",
    "curriculum_fact": "The cotton gin increased the demand for enslaved labor in the South.",
    "time_period": "1800-1848",
    "theme": "WXT"
  }
}
```

### Step 2: Generate Question

Your generator creates:
```json
{
  "stimulus": "\"The cotton gin has made the raising of cotton so profitable that whole regions of the South are being converted to its cultivation. The demand for laborers has increased proportionally.\" — Southern Agricultural Journal, 1820",
  "stem": "The development described in the excerpt most directly contributed to which of the following?",
  "choices": {
    "A": "The expansion of plantation agriculture and increased demand for enslaved labor",
    "B": "The decline of the Atlantic slave trade due to domestic labor surplus",
    "C": "The rise of industrial manufacturing in Southern port cities",
    "D": "The gradual emancipation of enslaved people in border states"
  },
  "correct_answer": "A",
  "explanation": "The cotton gin made cotton cultivation highly profitable, leading to the expansion of plantation agriculture westward and dramatically increasing the demand for enslaved labor to work the cotton fields."
}
```

### Step 3: Submit for Evaluation

```bash
curl -X POST http://192.168.1.27:8080/evaluate \
  -H "Content-Type: application/json" \
  -d '{
    "type": "mcq",
    "difficulty": "medium",
    "request": {
      "node_id": "c_Ab12",
      "course": "APUSH",
      "unit": 4,
      "topic": "The Society of the South in the Early Republic",
      "learning_objective": "Explain the causes and effects of the expansion of slavery.",
      "curriculum_fact": "The cotton gin increased the demand for enslaved labor in the South.",
      "time_period": "1800-1848",
      "theme": "WXT"
    },
    "output": {
      "stimulus": "\"The cotton gin has made the raising of cotton so profitable...\" — Southern Agricultural Journal, 1820",
      "stem": "The development described in the excerpt most directly contributed to which of the following?",
      "choices": {
        "A": "The expansion of plantation agriculture and increased demand for enslaved labor",
        "B": "The decline of the Atlantic slave trade due to domestic labor surplus",
        "C": "The rise of industrial manufacturing in Southern port cities",
        "D": "The gradual emancipation of enslaved people in border states"
      },
      "correct_answer": "A",
      "explanation": "The cotton gin made cotton cultivation highly profitable..."
    }
  }'
```

---

## Error Handling

### HTTP Status Codes

| Code | Meaning |
|------|---------|
| 200 | Success |
| 400 | Bad request - missing or invalid fields |
| 404 | No standards found matching criteria |
| 500 | Server error |

### Common Errors

**Missing required field:**
```json
{
  "success": false,
  "error": "Missing required fields: request.curriculum_fact",
  "received_fields": ["type", "difficulty", "request.node_id", "request.course", "output"],
  "documentation": "See GET / for full API documentation"
}
```

**Invalid type:**
```json
{
  "success": false,
  "error": "Invalid type 'multiple_choice'. Must be one of: mcq, mcq_set, saq, leq, dbq"
}
```

**Invalid output structure:**
```json
{
  "success": false,
  "error": "Invalid output for type 'mcq': output.choices.D is required; output.correct_answer must be A, B, C, or D",
  "documentation": "See GET / for output schema requirements"
}
```

---

## Python Client Example

```python
import requests

BASE_URL = "http://192.168.1.27:8080"

def generate_and_evaluate(question_type: str, difficulty: str, course: str = None):
    """Complete workflow: get standard, generate, evaluate."""

    # Step 1: Get a curriculum standard
    params = {}
    if course:
        params['course'] = course

    response = requests.get(f"{BASE_URL}/get_standard", params=params)
    data = response.json()

    if not data['success']:
        raise Exception(f"Failed to get standard: {data['error']}")

    standard = data['standard']
    print(f"Got standard: {standard['topic']} ({standard['course']} Unit {standard['unit']})")

    # Step 2: Generate question using YOUR generator
    generated_output = your_generator.generate(
        question_type=question_type,
        difficulty=difficulty,
        node_id=standard['node_id'],
        course=standard['course'],
        unit=standard['unit'],
        topic=standard['topic'],
        learning_objective=standard['learning_objective'],
        curriculum_fact=standard['curriculum_fact'],
        time_period=standard['time_period'],
        theme=standard['theme']
    )

    # Step 3: Submit for evaluation
    eval_response = requests.post(
        f"{BASE_URL}/evaluate",
        json={
            "type": question_type,
            "difficulty": difficulty,
            "request": standard,  # Pass the EXACT standard
            "output": generated_output
        }
    )

    result = eval_response.json()

    if not result['success']:
        raise Exception(f"Evaluation error: {result['error']}")

    print(f"Passed: {result['passed']}")
    print(f"Score: {result['overall_score']}")

    if result['issues']:
        print("Issues:")
        for issue in result['issues']:
            print(f"  - [{issue['severity']}] {issue['dimension']}: {issue['explanation'][:100]}...")

    return result


# Usage
result = generate_and_evaluate("mcq", "medium", course="APUSH")
```

---

## Contact

For questions about this API or evaluation criteria, contact the benchmark team.

**API Server:** `http://192.168.1.27:8080`
**Documentation:** `GET /`
**Health Check:** `GET /health`
