# AP Question Generator API Specification

**Version:** 2.0
**Status:** MANDATORY
**Last Updated:** 2026-02-26

---

## Overview

This document defines the **authoritative contract** between the benchmark evaluator and the AP Question Generator API. The generator MUST comply with this specification exactly. Non-compliance will result in benchmark failures and invalid evaluation data.

---

## Endpoint

```
POST /generate
Content-Type: application/json
```

---

## Request Schema

### Required Fields

| Field | Type | Description | Validation |
|-------|------|-------------|------------|
| `type` | string | Question type | MUST be one of: `mcq`, `mcq_set`, `saq`, `leq`, `dbq` |
| `course` | string | AP course identifier | MUST be one of: `APUSH`, `APWH` |
| `unit` | integer | Unit number | MUST be 1-9 for APUSH, 1-9 for APWH |
| `difficulty` | string | Difficulty level | MUST be one of: `easy`, `medium`, `hard` |

### Curriculum Context Fields (MUST BE USED IN GENERATION)

These fields contain the **specific curriculum standard** the question MUST be based on. The generator MUST incorporate ALL of these fields into its generation prompt. Ignoring these fields is a **critical violation**.

| Field | Type | Description | Generator Requirement |
|-------|------|-------------|----------------------|
| `node_id` | string | Unique curriculum standard identifier (e.g., `KC-1.1.I.A`, `KC-4.3.II.A.ii+1`) | MUST be echoed back unchanged. MUST NOT be transformed or auto-generated. |
| `learning_objective` | string | The specific AP learning objective text | MUST be incorporated into the generation prompt. Question MUST assess this objective. |
| `curriculum_fact` | string | The specific curriculum statement/fact from the knowledge schema | MUST be the primary content basis for the question. Question MUST be directly answerable using knowledge of this fact. |
| `time_period` | string | Historical time period (e.g., `1450-1750`, `1865-1898`) | MUST constrain the question's historical scope. All content MUST fall within this period. |
| `theme` | string | AP thematic category (e.g., `GEO`, `WOR`, `PCE`, `CUL`, `SOC`, `MIG`, `WXT`) | SHOULD influence question framing and skill emphasis. |
| `topic` | string | Topic/cluster name from curriculum | MUST be used for contextual framing. |

### Conditional Fields

| Field | Type | Condition | Description |
|-------|------|-----------|-------------|
| `reasoning_type` | string | Required when `type` = `leq` | MUST be one of: `causation`, `comparison`, `ccot` |

### Example Request

```json
{
  "type": "saq",
  "course": "APUSH",
  "unit": 3,
  "difficulty": "medium",
  "node_id": "KC-3.2.I.B",
  "learning_objective": "Explain how and why political ideas, institutions, and party systems developed and changed in the new republic.",
  "curriculum_fact": "The American two-party system emerged from the debates over the ratification of the Constitution and later from debates over the direction of the new nation, pitting Federalists against Democratic-Republicans.",
  "time_period": "1787-1820",
  "theme": "PCE",
  "topic": "The Rise of Political Parties and the Era of Jefferson"
}
```

---

## Response Schema

### Required Response Structure

```json
{
  "success": true,
  "request": { /* EXACT copy of request - see requirements below */ },
  "output": { /* Generated question content - see type-specific schemas */ },
  "generation_time_ms": 1234
}
```

### Request Echo Requirements

The `request` field in the response MUST contain an **exact copy** of all fields received in the request.

**CRITICAL VIOLATIONS:**
- ❌ Dropping fields (e.g., omitting `learning_objective`)
- ❌ Renaming fields (e.g., `curriculum_fact` → `statement`)
- ❌ Auto-generating values (e.g., creating `substandard_id` from `course` + `unit`)
- ❌ Transforming values (e.g., changing `node_id` format)

**CORRECT BEHAVIOR:**
- ✅ Echo all received fields with exact names and values
- ✅ If a field was not provided, omit it from the echo (do not add `null`)

### Error Response

```json
{
  "success": false,
  "error": "Descriptive error message",
  "request": { /* Echo of received request */ }
}
```

---

## Generation Requirements

### Curriculum Alignment (MANDATORY)

The generator MUST use the curriculum context fields to produce questions that are **precisely aligned** with the specified standard. This is not optional.

#### How to Use Each Field:

**`curriculum_fact`** (Primary Content Source)
- This is the MOST IMPORTANT field
- The generated question MUST be directly based on this fact
- A student who knows this fact MUST be able to answer the question correctly
- The question MUST NOT require knowledge outside the scope of this fact (except for scaffolding context)

**`learning_objective`** (Skill Target)
- The question MUST assess the skill described in this objective
- Use the action verbs in the objective to guide question construction (e.g., "Explain" → requires explanation, "Compare" → requires comparison)

**`time_period`** (Temporal Constraint)
- ALL historical content in the question MUST fall within this period
- Stimuli, documents, and answer choices MUST reference events/people/concepts from this period
- Do NOT reference events before or after this period unless explicitly asking about causes/effects that cross boundaries

**`node_id`** (Tracking Only)
- Echo back unchanged for tracking purposes
- Do NOT parse or interpret this field

**`theme`** (Framing Guidance)
- Use to influence the lens through which the question is framed
- GEO = Geography & Environment
- WOR = America & the World / World Interactions
- PCE = Politics & Power / Governance
- CUL = American & National Identity / Culture
- SOC = Social Structures
- MIG = Migration & Settlement
- WXT = Work, Exchange, Technology / Economics

---

## Output Schemas by Question Type

### MCQ (`type: "mcq"`)

```json
{
  "stimulus": "Primary source excerpt, image description, or contextual paragraph (REQUIRED for medium/hard difficulty)",
  "stem": "Question stem ending with a question mark",
  "choices": {
    "A": "First answer choice",
    "B": "Second answer choice",
    "C": "Third answer choice",
    "D": "Fourth answer choice"
  },
  "correct_answer": "A|B|C|D",
  "explanation": "Explanation of why the correct answer is correct and why distractors are incorrect"
}
```

**Requirements:**
- Exactly 4 answer choices (A, B, C, D)
- Exactly 1 correct answer
- Distractors MUST represent plausible student misconceptions, not absurd options
- Stimulus REQUIRED for medium/hard difficulty
- All content MUST align with `curriculum_fact` and `time_period`

### MCQ_SET (`type: "mcq_set"`)

```json
{
  "stimulus": "Extended primary source excerpt or document (REQUIRED)",
  "questions": [
    {
      "stem": "Question 1 stem",
      "choices": { "A": "...", "B": "...", "C": "...", "D": "..." },
      "correct_answer": "A|B|C|D",
      "explanation": "..."
    },
    {
      "stem": "Question 2 stem",
      "choices": { "A": "...", "B": "...", "C": "...", "D": "..." },
      "correct_answer": "A|B|C|D",
      "explanation": "..."
    },
    {
      "stem": "Question 3 stem",
      "choices": { "A": "...", "B": "...", "C": "...", "D": "..." },
      "correct_answer": "A|B|C|D",
      "explanation": "..."
    }
  ]
}
```

**Requirements:**
- Exactly 3 questions per set
- Shared stimulus REQUIRED
- ALL questions MUST require analysis of the stimulus (not just recall)
- Questions should test different skills (e.g., sourcing, contextualization, argumentation)

### SAQ (`type: "saq"`)

```json
{
  "stimulus": "Optional primary source, image, or data (recommended for hard difficulty)",
  "preamble": "Brief contextual framing (1-2 sentences)",
  "parts": {
    "a": {
      "prompt": "Part (a) question text",
      "skill": "Skill being assessed (e.g., 'Identify', 'Explain', 'Compare')",
      "scoring_notes": "What constitutes a complete answer"
    },
    "b": {
      "prompt": "Part (b) question text",
      "skill": "Skill being assessed",
      "scoring_notes": "What constitutes a complete answer"
    },
    "c": {
      "prompt": "Part (c) question text",
      "skill": "Skill being assessed",
      "scoring_notes": "What constitutes a complete answer"
    }
  }
}
```

**Requirements:**
- Exactly 3 parts (a, b, c)
- Parts MUST be scaffolded (build on each other OR test related aspects)
- Use varied task verbs across parts (not all "Identify")
- Part (a) may use lower-order verb; parts (b) and (c) should require higher-order thinking
- All parts MUST be answerable based on `curriculum_fact` + reasonable outside knowledge

### LEQ (`type: "leq"`)

```json
{
  "prompt": "Full LEQ prompt text with time period and clear arguable claim",
  "reasoning_type": "causation|comparison|ccot",
  "time_period_explicit": "The time period stated in the prompt (e.g., '1800-1848')",
  "scoring_guidance": {
    "thesis_examples": ["Example strong thesis 1", "Example strong thesis 2"],
    "contextualization_notes": "What historical context is relevant",
    "evidence_expectations": "What specific evidence students might cite",
    "complexity_paths": ["Way to earn complexity point 1", "Way to earn complexity point 2"]
  }
}
```

**Requirements:**
- Prompt MUST contain explicit time period boundaries
- Prompt MUST be arguable (reasonable people could disagree)
- `reasoning_type` MUST match the request
- Prompt MUST use standard AP phrasing ("Evaluate the extent to which...")
- Time period MUST align with `time_period` from request

### DBQ (`type: "dbq"`)

```json
{
  "prompt": "Full DBQ prompt text with time period and arguable claim",
  "documents": [
    {
      "number": 1,
      "source": "Full attribution: Author, Title, Date",
      "type": "letter|speech|government document|newspaper|diary|treaty|image|map|chart|etc.",
      "content": "Full document text or image description",
      "historical_context": "Brief context for teacher reference",
      "sourcing_notes": "HIPP analysis opportunities (Historical situation, Intended audience, Purpose, POV)"
    }
    // ... 7 documents total
  ],
  "scoring_guidance": {
    "thesis_examples": ["Example thesis 1", "Example thesis 2"],
    "document_groupings": ["Possible grouping 1", "Possible grouping 2"],
    "outside_evidence": ["Relevant outside evidence 1", "Relevant outside evidence 2"],
    "complexity_paths": ["Complexity approach 1", "Complexity approach 2"]
  }
}
```

**Requirements:**
- Exactly 7 documents
- ALL documents MUST be authentic historical sources or clearly adapted from authentic sources
- Each document MUST have full attribution (Author, Title, Date)
- Documents MUST span multiple perspectives/viewpoints
- Documents MUST be from the `time_period` specified in the request
- At least 2 document types should be represented
- Documents MUST be relevant to `curriculum_fact` and support argumentation

---

## Validation Rules

The generator MUST validate requests and return appropriate errors:

| Validation | Error Response |
|------------|----------------|
| Missing `type` | `{"success": false, "error": "Missing required field: type"}` |
| Invalid `type` value | `{"success": false, "error": "Invalid type. Must be one of: mcq, mcq_set, saq, leq, dbq"}` |
| Missing `course` | `{"success": false, "error": "Missing required field: course"}` |
| `type: "leq"` without `reasoning_type` | `{"success": false, "error": "reasoning_type is required for LEQ questions"}` |
| Missing curriculum context | `{"success": false, "error": "Missing curriculum context. Required: learning_objective, curriculum_fact"}` |

---

## Anti-Patterns (MUST NOT DO)

### 1. Auto-Generating IDs
```json
// ❌ WRONG - Generator creates its own ID
"request": {
  "substandard_id": "USH.1.1"  // Auto-generated, not from request
}

// ✅ CORRECT - Generator echoes exactly what was sent
"request": {
  "node_id": "KC-1.1.I.A"  // Exact value from request
}
```

### 2. Dropping Fields
```json
// ❌ WRONG - Missing fields from echo
"request": {
  "type": "mcq",
  "course": "APUSH"
  // learning_objective, curriculum_fact, time_period all missing!
}

// ✅ CORRECT - All fields echoed
"request": {
  "type": "mcq",
  "course": "APUSH",
  "learning_objective": "...",
  "curriculum_fact": "...",
  "time_period": "...",
  "node_id": "..."
}
```

### 3. Ignoring Curriculum Context
```json
// ❌ WRONG - Question unrelated to curriculum_fact
// Request: curriculum_fact = "The Stamp Act of 1765 imposed direct taxes on the colonies"
// Generated question asks about the Boston Tea Party (different event)

// ✅ CORRECT - Question directly tests the curriculum_fact
// Generated question asks about the Stamp Act and colonial response to direct taxation
```

### 4. Time Period Violations
```json
// ❌ WRONG - Content outside time period
// Request: time_period = "1765-1776"
// Generated question mentions the War of 1812

// ✅ CORRECT - All content within time period
// Question and all answer choices reference events from 1765-1776
```

---

## Testing Compliance

To verify generator compliance, send this test request:

```json
{
  "type": "mcq",
  "course": "APUSH",
  "unit": 1,
  "difficulty": "medium",
  "node_id": "TEST-NODE-12345",
  "learning_objective": "TEST-LO-OBJECTIVE",
  "curriculum_fact": "TEST-CURRICULUM-FACT",
  "time_period": "1492-1607",
  "theme": "GEO",
  "topic": "Test Topic"
}
```

**Expected response `request` field:**
```json
{
  "type": "mcq",
  "course": "APUSH",
  "unit": 1,
  "difficulty": "medium",
  "node_id": "TEST-NODE-12345",
  "learning_objective": "TEST-LO-OBJECTIVE",
  "curriculum_fact": "TEST-CURRICULUM-FACT",
  "time_period": "1492-1607",
  "theme": "GEO",
  "topic": "Test Topic"
}
```

If any field is missing, renamed, or has a different value, the generator is **non-compliant**.

---

## Changelog

| Version | Date | Changes |
|---------|------|---------|
| 2.0 | 2026-02-26 | Complete rewrite. Added strict curriculum context requirements. Deprecated `statement` (use `curriculum_fact`), deprecated `substandard_id` (use `node_id`). |
| 1.0 | Legacy | Original loose specification |

---

## Contact

For questions about this specification, contact the benchmark team. Non-compliance issues should be filed as blocking bugs.
