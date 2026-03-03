#!/usr/bin/env python3
"""
AP Question Evaluation Server v2.0

Provides endpoints for:
- GET  /                - API documentation and info
- GET  /health          - Health check
- GET  /get_standard    - Get a random curriculum standard
- GET  /get_standards   - Get multiple random standards
- POST /evaluate        - Evaluate a generated question (requires standard from /get_standard)

Run with: python evaluation_server.py
Server binds to 0.0.0.0:8080 for local network access
"""

import json
import os
import random
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

import anthropic
from flask import Flask, jsonify, request, Response
from flask_cors import CORS
from pymongo import MongoClient

# Load environment
from dotenv import load_dotenv
load_dotenv()

# Import official AP prompts and formatters
from ap_benchmark.prompts.official_ap_prompts import (
    MCQ_EVALUATION_PROMPT,
    MCQ_SET_EVALUATION_PROMPT,
    SAQ_EVALUATION_PROMPT,
    DBQ_EVALUATION_PROMPT,
    LEQ_EVALUATION_PROMPT,
    PROMPT_VERSION,
)
from ap_benchmark.prompts.official_ap_formatters import format_question_content

# Configuration
MONGODB_URI = os.environ.get('MONGODB_URI')
if not MONGODB_URI:
    raise ValueError("MONGODB_URI environment variable is required")

DB_NAME = "ap_social_studies"
SERVER_HOST = "0.0.0.0"
SERVER_PORT = 8080
API_VERSION = "2.0.0"

# Question types
VALID_QUESTION_TYPES = ["mcq", "mcq_set", "saq", "leq", "dbq"]
VALID_COURSES = ["APUSH", "APWH"]
VALID_DIFFICULTIES = ["easy", "medium", "hard"]

# Initialize Flask app
app = Flask(__name__)
CORS(app)

# Initialize Anthropic client
anthropic_client = anthropic.Anthropic()


def get_db():
    """Get MongoDB database connection."""
    client = MongoClient(MONGODB_URI, serverSelectionTimeoutMS=10000)
    return client[DB_NAME]


def validate_required_fields(data: dict, required: List[str]) -> Optional[str]:
    """Validate that all required fields are present and non-empty."""
    missing = []
    for field in required:
        if field not in data:
            missing.append(field)
        elif data[field] is None or data[field] == "":
            missing.append(f"{field} (empty)")
    if missing:
        return f"Missing required fields: {', '.join(missing)}"
    return None


# ============================================
# GET / - API Documentation
# ============================================

API_DOCUMENTATION = """
# AP Question Evaluation API

**Version:** {version}
**Evaluator Version:** {evaluator_version}
**Base URL:** http://{{host}}:8080

---

## Overview

This API provides curriculum standards for AP question generation and evaluates
generated questions against official AP rubrics.

**Workflow:**
1. Call `GET /get_standard` to receive a curriculum standard
2. Generate a question based on that standard
3. Call `POST /evaluate` with the original request and generated output

---

## Endpoints

### `GET /health`

Health check endpoint.

**Response:**
```json
{{
  "status": "healthy",
  "api_version": "{version}",
  "evaluator_version": "{evaluator_version}",
  "timestamp": "2026-02-26T15:00:00Z"
}}
```

---

### `GET /get_standard`

Get a random curriculum standard for question generation.

**Query Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `course` | string | No | Filter by course: `APUSH` or `APWH` |
| `unit` | integer | No | Filter by unit number (1-9) |

**Response:**
```json
{{
  "success": true,
  "standard": {{
    "node_id": "KC-4.1.II.A",
    "course": "APUSH",
    "unit": 4,
    "topic": "The Rise of Political Parties",
    "learning_objective": "Explain how and why political ideas changed...",
    "curriculum_fact": "The American two-party system emerged from debates...",
    "time_period": "1787-1820",
    "theme": "PCE"
  }}
}}
```

**IMPORTANT:** The `standard` object returned MUST be used as the `request` field
when calling `/evaluate`. Do not modify or omit any fields.

---

### `GET /get_standards`

Get multiple random curriculum standards.

**Query Parameters:**

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `count` | integer | No | 5 | Number of standards (max 50) |
| `course` | string | No | - | Filter by course |

**Response:**
```json
{{
  "success": true,
  "count": 5,
  "standards": [
    {{ "node_id": "...", "course": "...", ... }},
    ...
  ]
}}
```

---

### `POST /evaluate`

Evaluate a generated AP question against official rubrics.

**CRITICAL REQUIREMENTS:**
1. The `request` field MUST contain the EXACT standard returned by `/get_standard`
2. The `type` field MUST match what was used for generation
3. The `output` field MUST contain the generated question content

**Request Body:**

```json
{{
  "type": "mcq|mcq_set|saq|leq|dbq",
  "difficulty": "easy|medium|hard",
  "request": {{
    "node_id": "KC-4.1.II.A",
    "course": "APUSH",
    "unit": 4,
    "topic": "The Rise of Political Parties",
    "learning_objective": "Explain how and why political ideas changed...",
    "curriculum_fact": "The American two-party system emerged from debates...",
    "time_period": "1787-1820",
    "theme": "PCE"
  }},
  "output": {{
    // Question content - schema depends on type (see below)
  }}
}}
```

**Required Fields:**

| Field | Type | Description |
|-------|------|-------------|
| `type` | string | Question type: `mcq`, `mcq_set`, `saq`, `leq`, `dbq` |
| `difficulty` | string | Difficulty level: `easy`, `medium`, `hard` |
| `request` | object | **EXACT** standard from `/get_standard` |
| `request.node_id` | string | Curriculum node identifier |
| `request.course` | string | `APUSH` or `APWH` |
| `request.unit` | integer | Unit number (1-9) |
| `request.topic` | string | Topic/cluster name |
| `request.learning_objective` | string | Learning objective text |
| `request.curriculum_fact` | string | Curriculum fact/statement |
| `request.time_period` | string | Historical time period |
| `request.theme` | string | AP thematic category |
| `output` | object | Generated question content |

**Output Schemas by Type:**

#### MCQ Output
```json
{{
  "stimulus": "Primary source excerpt (REQUIRED for medium/hard)",
  "stem": "Question text ending with ?",
  "choices": {{
    "A": "First answer choice",
    "B": "Second answer choice",
    "C": "Third answer choice",
    "D": "Fourth answer choice"
  }},
  "correct_answer": "A|B|C|D",
  "explanation": "Why the correct answer is correct"
}}
```

#### MCQ_SET Output
```json
{{
  "stimulus": "Extended primary source (REQUIRED)",
  "questions": [
    {{
      "stem": "Question 1 text",
      "choices": {{ "A": "...", "B": "...", "C": "...", "D": "..." }},
      "correct_answer": "A|B|C|D",
      "explanation": "..."
    }},
    // Exactly 3 questions required
  ]
}}
```

#### SAQ Output
```json
{{
  "stimulus": "Optional primary source",
  "preamble": "Brief contextual framing",
  "parts": {{
    "a": {{
      "prompt": "Part (a) question text",
      "skill": "identify|describe|explain",
      "scoring_notes": "What constitutes a complete answer"
    }},
    "b": {{ "prompt": "...", "skill": "...", "scoring_notes": "..." }},
    "c": {{ "prompt": "...", "skill": "...", "scoring_notes": "..." }}
  }}
}}
```

#### LEQ Output
```json
{{
  "prompt": "Full LEQ prompt with time period",
  "reasoning_type": "causation|comparison|ccot",
  "time_period_explicit": "1800-1848",
  "scoring_guidance": {{
    "thesis_examples": ["Example thesis 1", "Example thesis 2"],
    "contextualization_notes": "Relevant historical context",
    "evidence_expectations": "Expected evidence",
    "complexity_paths": ["Way to earn complexity"]
  }}
}}
```

#### DBQ Output
```json
{{
  "prompt": "Full DBQ prompt with time period",
  "documents": [
    {{
      "number": 1,
      "source": "Author, Title, Date",
      "type": "letter|speech|government document|...",
      "content": "Document text or description",
      "historical_context": "Context for reference",
      "sourcing_notes": "HIPP analysis opportunities"
    }}
    // Exactly 7 documents required
  ],
  "scoring_guidance": {{
    "thesis_examples": ["..."],
    "document_groupings": ["..."],
    "outside_evidence": ["..."],
    "complexity_paths": ["..."]
  }}
}}
```

**Success Response:**
```json
{{
  "success": true,
  "passed": true,
  "overall_score": 0.92,
  "critical_failed": false,
  "dimensions": {{
    "answer_validity": {{ "score": 1.0, "reasoning": "..." }},
    "clarity": {{ "score": 1.0, "reasoning": "..." }},
    ...
  }},
  "issues": [
    {{
      "id": "ISSUE1",
      "dimension": "distractor_quality",
      "severity": "minor",
      "snippet": "...",
      "explanation": "..."
    }}
  ],
  "overall_assessment": "PASS - Well-constructed question...",
  "evaluator_version": "{evaluator_version}"
}}
```

**Error Response:**
```json
{{
  "success": false,
  "error": "Missing required fields: request.curriculum_fact",
  "received_fields": ["type", "output", "request.course"]
}}
```

---

## Evaluation Dimensions

Questions are evaluated on these dimensions (varies by type):

### MCQ / MCQ_SET Dimensions
| Dimension | Description |
|-----------|-------------|
| `answer_validity` | Exactly one unambiguously correct answer |
| `factual_accuracy` | All content historically accurate |
| `stimulus_alignment` | Question requires analysis of stimulus |
| `distractor_quality` | Wrong answers are plausible but clearly wrong |
| `skill_alignment` | Tests appropriate AP skill |
| `clarity` | Clear, unambiguous wording |

### SAQ Dimensions
| Dimension | Description |
|-----------|-------------|
| `prompt_structure` | Exactly 3 parts (a, b, c) |
| `historical_specificity` | Grounded in specific historical content |
| `answerability` | Can be answered with AP course knowledge |
| `skill_alignment` | Appropriate task verbs (identify/describe/explain) |
| `stimulus_integration` | Parts properly use any stimulus |
| `scoring_clarity` | Clear scoring guidance |

### LEQ Dimensions
| Dimension | Description |
|-----------|-------------|
| `prompt_arguability` | Supports arguable thesis |
| `reasoning_type` | Matches requested type (causation/comparison/ccot) |
| `time_period_specificity` | Clear, appropriate time bounds |
| `evidence_accessibility` | Students can cite relevant evidence |
| `thesis_flexibility` | Multiple valid thesis approaches |
| `complexity_opportunity` | Path to earn complexity point |

### DBQ Dimensions
| Dimension | Description |
|-----------|-------------|
| `document_count` | Exactly 7 documents |
| `document_authenticity` | Authentic sources with proper attribution |
| `document_diversity` | Multiple perspectives and types |
| `document_relevance` | All docs relevant to prompt |
| `prompt_arguability` | Supports arguable thesis |
| `sourcing_opportunity` | Documents allow HIPP analysis |

---

## Hard Fail Dimensions

These dimensions cause automatic failure if score < 1.0:

- `document_count` (DBQ must have exactly 7 documents)
- `prompt_structure` (SAQ must have exactly 3 parts)
- `factual_accuracy` (No factual errors allowed)
- `answer_validity` (MCQ must have exactly 1 correct answer)

---

## Pass/Fail Criteria

A question **PASSES** if:
1. No hard-fail dimensions have score < 1.0
2. Overall score >= 0.70

---

## Example Workflow

```python
import requests

BASE_URL = "http://192.168.1.27:8080"

# Step 1: Get a curriculum standard
response = requests.get(f"{{BASE_URL}}/get_standard", params={{"course": "APUSH"}})
data = response.json()
standard = data["standard"]

# Step 2: Generate question (your generator)
generated_output = your_generator.generate(
    type="mcq",
    difficulty="medium",
    **standard  # Pass all standard fields to generator
)

# Step 3: Submit for evaluation
eval_response = requests.post(
    f"{{BASE_URL}}/evaluate",
    json={{
        "type": "mcq",
        "difficulty": "medium",
        "request": standard,  # MUST be exact standard from step 1
        "output": generated_output
    }}
)

result = eval_response.json()
print(f"Passed: {{result['passed']}}")
print(f"Score: {{result['overall_score']}}")
```

---

## Error Codes

| HTTP Code | Meaning |
|-----------|---------|
| 200 | Success |
| 400 | Bad request (missing/invalid fields) |
| 404 | No standards found matching criteria |
| 500 | Server error |

---

## Contact

For questions about this API, contact the benchmark team.
"""


@app.route('/', methods=['GET'])
def index():
    """Return API documentation."""
    # Check if client wants JSON
    if request.headers.get('Accept') == 'application/json':
        return jsonify({
            "name": "AP Question Evaluation API",
            "api_version": API_VERSION,
            "evaluator_version": PROMPT_VERSION,
            "documentation": "GET / with Accept: text/markdown for full docs",
            "endpoints": {
                "GET /": "API documentation",
                "GET /health": "Health check",
                "GET /get_standard": "Get random curriculum standard",
                "GET /get_standards": "Get multiple standards",
                "POST /evaluate": "Evaluate a question",
            },
            "question_types": VALID_QUESTION_TYPES,
            "courses": VALID_COURSES,
            "difficulties": VALID_DIFFICULTIES,
        })

    # Return markdown documentation
    doc = API_DOCUMENTATION.format(
        version=API_VERSION,
        evaluator_version=PROMPT_VERSION
    )
    return Response(doc, mimetype='text/markdown')


# ============================================
# GET /health
# ============================================

@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint."""
    return jsonify({
        "status": "healthy",
        "api_version": API_VERSION,
        "evaluator_version": PROMPT_VERSION,
        "timestamp": datetime.now(timezone.utc).isoformat()
    })


# ============================================
# GET /get_standard
# ============================================

@app.route('/get_standard', methods=['GET'])
def get_standard():
    """
    Get a random curriculum standard for question generation.
    """
    try:
        db = get_db()

        # Build filter from query params
        query = {}
        if request.args.get('course'):
            course = request.args.get('course').upper()
            if course not in VALID_COURSES:
                return jsonify({
                    "success": False,
                    "error": f"Invalid course. Must be one of: {', '.join(VALID_COURSES)}"
                }), 400
            query['course'] = course

        if request.args.get('unit'):
            try:
                unit = int(request.args.get('unit'))
                if unit < 1 or unit > 9:
                    return jsonify({
                        "success": False,
                        "error": "Unit must be between 1 and 9"
                    }), 400
                query['unit'] = unit
            except ValueError:
                return jsonify({
                    "success": False,
                    "error": "Unit must be an integer"
                }), 400

        # Get random standard
        pipeline = [{"$match": query}] if query else []
        pipeline.append({"$sample": {"size": 1}})

        results = list(db.facts.aggregate(pipeline))

        if not results:
            return jsonify({
                "success": False,
                "error": "No standards found matching criteria"
            }), 404

        fact = results[0]

        # Format response - these fields are REQUIRED for /evaluate
        standard = {
            "node_id": str(fact.get("node_id", fact.get("_id", ""))),
            "course": fact.get("course", "APUSH"),
            "unit": int(fact.get("unit", 1)) if fact.get("unit") else 1,
            "topic": fact.get("cluster", "") or "",
            "learning_objective": fact.get("learning_objective", "") or "",
            "curriculum_fact": fact.get("statement", "") or "",
            "time_period": fact.get("date", "") or "",
            "theme": fact.get("theme", "") or "",
        }

        return jsonify({
            "success": True,
            "standard": standard,
            "_usage": "Pass this 'standard' object as 'request' field when calling POST /evaluate"
        })

    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@app.route('/get_standards', methods=['GET'])
def get_standards():
    """Get multiple random curriculum standards."""
    try:
        db = get_db()

        count = min(int(request.args.get('count', 5)), 50)

        query = {}
        if request.args.get('course'):
            course = request.args.get('course').upper()
            if course not in VALID_COURSES:
                return jsonify({
                    "success": False,
                    "error": f"Invalid course. Must be one of: {', '.join(VALID_COURSES)}"
                }), 400
            query['course'] = course

        pipeline = [{"$match": query}] if query else []
        pipeline.append({"$sample": {"size": count}})

        results = list(db.facts.aggregate(pipeline))

        standards = []
        for fact in results:
            standards.append({
                "node_id": str(fact.get("node_id", fact.get("_id", ""))),
                "course": fact.get("course", "APUSH"),
                "unit": int(fact.get("unit", 1)) if fact.get("unit") else 1,
                "topic": fact.get("cluster", "") or "",
                "learning_objective": fact.get("learning_objective", "") or "",
                "curriculum_fact": fact.get("statement", "") or "",
                "time_period": fact.get("date", "") or "",
                "theme": fact.get("theme", "") or "",
            })

        return jsonify({
            "success": True,
            "count": len(standards),
            "standards": standards
        })

    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


# ============================================
# POST /evaluate
# ============================================

def get_evaluation_prompt(qtype: str) -> str:
    """Get the official evaluation prompt for a question type."""
    prompts = {
        "mcq": MCQ_EVALUATION_PROMPT,
        "mcq_set": MCQ_SET_EVALUATION_PROMPT,
        "saq": SAQ_EVALUATION_PROMPT,
        "leq": LEQ_EVALUATION_PROMPT,
        "dbq": DBQ_EVALUATION_PROMPT,
    }
    return prompts.get(qtype.lower(), MCQ_EVALUATION_PROMPT)


def build_curriculum_context(req: Dict) -> str:
    """Build curriculum context string for evaluation."""
    return f"""**Course:** {req.get('course', 'N/A')}
**Unit:** {req.get('unit', 'N/A')}
**Topic:** {req.get('topic', 'N/A')}
**Learning Objective:** {req.get('learning_objective', 'N/A')}
**Curriculum Fact:** {req.get('curriculum_fact', 'N/A')}
**Time Period:** {req.get('time_period', 'N/A')}
**Theme:** {req.get('theme', 'N/A')}
**Node ID:** {req.get('node_id', 'N/A')}"""


@app.route('/evaluate', methods=['POST'])
def evaluate():
    """
    Evaluate a generated AP question against official rubrics.

    REQUIRED REQUEST BODY:
    {
        "type": "mcq|mcq_set|saq|leq|dbq",
        "difficulty": "easy|medium|hard",
        "request": { ... exact standard from /get_standard ... },
        "output": { ... generated question content ... }
    }
    """
    try:
        data = request.get_json()

        if not data:
            return jsonify({
                "success": False,
                "error": "No JSON body provided. See GET / for documentation."
            }), 400

        # ========================================
        # STRICT VALIDATION
        # ========================================

        errors = []
        received_fields = list(data.keys())

        # Validate type
        qtype = data.get('type', '').lower()
        if not qtype:
            errors.append("Missing required field: type")
        elif qtype not in VALID_QUESTION_TYPES:
            errors.append(f"Invalid type '{qtype}'. Must be one of: {', '.join(VALID_QUESTION_TYPES)}")

        # Validate difficulty
        difficulty = data.get('difficulty', '').lower()
        if not difficulty:
            errors.append("Missing required field: difficulty")
        elif difficulty not in VALID_DIFFICULTIES:
            errors.append(f"Invalid difficulty '{difficulty}'. Must be one of: {', '.join(VALID_DIFFICULTIES)}")

        # Validate request (the standard from /get_standard)
        req = data.get('request')
        if not req:
            errors.append("Missing required field: request (must be the standard from GET /get_standard)")
        elif not isinstance(req, dict):
            errors.append("Field 'request' must be an object")
        else:
            # Validate required request fields
            required_request_fields = [
                'node_id', 'course', 'unit', 'topic',
                'learning_objective', 'curriculum_fact', 'time_period', 'theme'
            ]
            for field in required_request_fields:
                if field not in req:
                    errors.append(f"Missing required field: request.{field}")
                    received_fields.append(f"request.{field} (MISSING)")
                else:
                    received_fields.append(f"request.{field}")

            # Validate course
            if req.get('course') and req.get('course') not in VALID_COURSES:
                errors.append(f"Invalid request.course '{req.get('course')}'. Must be one of: {', '.join(VALID_COURSES)}")

        # Validate output
        output = data.get('output')
        if not output:
            errors.append("Missing required field: output (the generated question content)")
        elif not isinstance(output, dict):
            errors.append("Field 'output' must be an object containing the generated question")

        # Return all validation errors
        if errors:
            return jsonify({
                "success": False,
                "error": "; ".join(errors),
                "received_fields": received_fields,
                "documentation": "See GET / for full API documentation"
            }), 400

        # ========================================
        # TYPE-SPECIFIC OUTPUT VALIDATION
        # ========================================

        output_errors = []

        if qtype == "mcq":
            if not output.get('stem'):
                output_errors.append("output.stem is required")
            if not output.get('choices'):
                output_errors.append("output.choices is required")
            elif isinstance(output.get('choices'), dict):
                for key in ['A', 'B', 'C', 'D']:
                    if key not in output['choices']:
                        output_errors.append(f"output.choices.{key} is required")
            if not output.get('correct_answer'):
                output_errors.append("output.correct_answer is required")
            elif output.get('correct_answer') not in ['A', 'B', 'C', 'D']:
                output_errors.append("output.correct_answer must be A, B, C, or D")

        elif qtype == "mcq_set":
            if not output.get('stimulus'):
                output_errors.append("output.stimulus is required for mcq_set")
            if not output.get('questions'):
                output_errors.append("output.questions is required")
            elif not isinstance(output.get('questions'), list):
                output_errors.append("output.questions must be an array")
            elif len(output.get('questions', [])) < 3 or len(output.get('questions', [])) > 4:
                output_errors.append(f"output.questions must have 3-4 items (got {len(output.get('questions', []))})")

        elif qtype == "saq":
            if not output.get('parts'):
                output_errors.append("output.parts is required")
            elif isinstance(output.get('parts'), dict):
                for part in ['a', 'b', 'c']:
                    if part not in output['parts']:
                        output_errors.append(f"output.parts.{part} is required")

        elif qtype == "leq":
            if not output.get('prompt'):
                output_errors.append("output.prompt is required")
            if not output.get('reasoning_type'):
                output_errors.append("output.reasoning_type is required")
            elif output.get('reasoning_type') not in ['causation', 'comparison', 'ccot']:
                output_errors.append("output.reasoning_type must be causation, comparison, or ccot")

        elif qtype == "dbq":
            if not output.get('prompt'):
                output_errors.append("output.prompt is required")
            if not output.get('documents'):
                output_errors.append("output.documents is required")
            elif not isinstance(output.get('documents'), list):
                output_errors.append("output.documents must be an array")
            elif len(output.get('documents', [])) != 7:
                output_errors.append(f"output.documents must have exactly 7 items (got {len(output.get('documents', []))})")

        if output_errors:
            return jsonify({
                "success": False,
                "error": f"Invalid output for type '{qtype}': " + "; ".join(output_errors),
                "documentation": "See GET / for output schema requirements"
            }), 400

        # ========================================
        # PERFORM EVALUATION
        # ========================================

        # Get evaluation prompt template
        prompt_template = get_evaluation_prompt(qtype)

        # Format question content
        question_content = format_question_content(output, qtype)

        # Build curriculum context from the request
        curriculum_context = build_curriculum_context(req)

        # Add difficulty to context
        curriculum_context += f"\n**Requested Difficulty:** {difficulty}"

        # Build full evaluation prompt
        full_prompt = prompt_template.format(
            curriculum_context=curriculum_context,
            question_content=question_content
        )

        # Call Claude for evaluation
        response = anthropic_client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=8000,
            messages=[{"role": "user", "content": full_prompt}]
        )

        text = response.content[0].text

        # Extract JSON from response
        if "```json" in text:
            json_str = text.split("```json")[1].split("```")[0]
        elif "```" in text:
            json_str = text.split("```")[1].split("```")[0]
        else:
            json_str = text

        result = json.loads(json_str.strip())

        # Calculate overall score
        dimensions = result.get("dimensions", {})
        scores = []
        for dim_data in dimensions.values():
            if isinstance(dim_data, dict):
                scores.append(dim_data.get("score", 0))
            else:
                scores.append(float(dim_data) if dim_data else 0)

        overall_score = sum(scores) / len(scores) if scores else 0

        # Check for hard failures
        hard_fail_dims = {
            "document_count",
            "prompt_structure",
            "factual_accuracy",
            "answer_validity",
        }

        critical_failed = False
        failed_hard_dims = []
        for dim_name in hard_fail_dims:
            if dim_name in dimensions:
                dim_data = dimensions[dim_name]
                score = dim_data.get("score", 1.0) if isinstance(dim_data, dict) else dim_data
                if score < 1.0:
                    critical_failed = True
                    failed_hard_dims.append(dim_name)

        # Determine pass/fail
        passed = not critical_failed and overall_score >= 0.70

        # Verbose logging
        import sys
        status_emoji = "✅" if passed else "❌"
        print(f"\n{'='*60}", flush=True)
        print(f"{status_emoji} EVALUATION: {qtype.upper()} | {req.get('course')} | {difficulty}", flush=True)
        print(f"   Node ID: {req.get('node_id')}", flush=True)
        print(f"   Topic: {req.get('topic')}", flush=True)
        print(f"   Score: {overall_score:.2f} | Passed: {passed}", flush=True)
        if critical_failed:
            print(f"   ⚠️  Hard-fail dimensions: {', '.join(failed_hard_dims)}", flush=True)
        if result.get("issues"):
            print(f"   Issues: {len(result.get('issues', []))}", flush=True)
            for issue in result.get("issues", [])[:3]:
                if isinstance(issue, dict):
                    print(f"      - {issue.get('dimension', '?')}: {issue.get('issue', str(issue))[:80]}", flush=True)
                else:
                    print(f"      - {str(issue)[:80]}", flush=True)
        print(f"{'='*60}\n", flush=True)
        sys.stdout.flush()

        return jsonify({
            "success": True,
            "passed": passed,
            "overall_score": round(overall_score, 3),
            "critical_failed": critical_failed,
            "failed_hard_dimensions": failed_hard_dims if critical_failed else [],
            "dimensions": dimensions,
            "issues": result.get("issues", []),
            "overall_assessment": result.get("overall_assessment", ""),
            "evaluator_version": PROMPT_VERSION,
            "evaluated_at": datetime.now(timezone.utc).isoformat(),
            "request_echo": {
                "type": qtype,
                "difficulty": difficulty,
                "node_id": req.get('node_id'),
                "course": req.get('course'),
            }
        })

    except json.JSONDecodeError as e:
        return jsonify({
            "success": False,
            "error": f"Failed to parse evaluation response: {str(e)}",
            "raw_response": text[:1000] if 'text' in dir() else None
        }), 500

    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


# ============================================
# Main
# ============================================

if __name__ == "__main__":
    import socket

    hostname = socket.gethostname()
    try:
        local_ip = socket.gethostbyname(hostname)
    except:
        local_ip = "127.0.0.1"

    print(f"""
╔══════════════════════════════════════════════════════════════╗
║           AP Question Evaluation Server v{API_VERSION}                ║
╠══════════════════════════════════════════════════════════════╣
║  Local:    http://127.0.0.1:{SERVER_PORT}                             ║
║  Network:  http://{local_ip}:{SERVER_PORT}                           ║
╠══════════════════════════════════════════════════════════════╣
║  Endpoints:                                                   ║
║    GET  /               - API documentation                   ║
║    GET  /health         - Health check                        ║
║    GET  /get_standard   - Get random curriculum standard      ║
║    GET  /get_standards  - Get multiple standards              ║
║    POST /evaluate       - Evaluate a question                 ║
╠══════════════════════════════════════════════════════════════╣
║  Evaluator Version: {PROMPT_VERSION}                           ║
╚══════════════════════════════════════════════════════════════╝

Documentation: curl http://localhost:{SERVER_PORT}/
""")

    app.run(host=SERVER_HOST, port=SERVER_PORT, debug=False, threaded=True)
