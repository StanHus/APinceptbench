# Generator Output Specification

JSON output formats for each question type.

## MCQ

```json
{
  "type": "mcq",
  "stimulus": {
    "type": "primary_source|secondary_source|image|map|chart",
    "source": "Author/Publication",
    "date": "1850",
    "content": "50-300 words"
  },
  "question": "10-50 words",
  "answer_options": [
    {"key": "A", "text": "5-40 words"},
    {"key": "B", "text": "..."},
    {"key": "C", "text": "..."},
    {"key": "D", "text": "..."}
  ],
  "answer": "B",
  "explanation": "50-150 words",
  "skill": "causation|comparison|contextualization|sourcing"
}
```

**Rules**: 4 options, 1 correct, plausible distractors, parallel structure, no absolutes

## MCQ Set

```json
{
  "type": "mcq_set",
  "stimulus": { /* same as MCQ */ },
  "questions": [
    { "question": "...", "answer_options": [...], "answer": "A", "explanation": "...", "skill": "..." },
    { /* 2-3 more questions */ }
  ]
}
```

**Rules**: 3-4 questions, different skills, independent answers

## SAQ

```json
{
  "type": "saq",
  "stimulus": { /* optional */ },
  "prompt": "Answer parts (a), (b), and (c).",
  "parts": [
    {
      "letter": "a",
      "task": "Identify ONE...",
      "task_verb": "identify|describe|explain",
      "scoring_criteria": "Acceptable: ...",
      "sample_response": "30-75 words"
    },
    { "letter": "b", /* ... */ },
    { "letter": "c", /* ... */ }
  ],
  "time_period": "1800-1848",
  "skill": "causation|comparison|contextualization"
}
```

**Rules**: exactly 3 parts, 1 point each, specific evidence required

## LEQ

```json
{
  "type": "leq",
  "prompt": "Evaluate the extent to which...",
  "time_period": "1800-1848",
  "reasoning_type": "causation|comparison|ccot",
  "thesis_positions": ["Position A", "Position B", "Position C"],
  "suggested_evidence": ["Evidence 1", "Evidence 2", "..."],
  "scoring_notes": "Rubric guidance"
}
```

**Rules**: arguable thesis, clear time bounds, multiple valid positions

## DBQ

```json
{
  "type": "dbq",
  "prompt": "Evaluate the extent to which...",
  "time_period": "1800-1848",
  "documents": [
    {
      "number": 1,
      "type": "primary_source|letter|speech|newspaper|image|map|chart",
      "source": "Full attribution",
      "author": "Name",
      "date": "Year",
      "content": "100-250 words",
      "perspective": "supports|challenges|complicates"
    }
    /* 7 documents total */
  ],
  "suggested_thesis_positions": ["..."],
  "suggested_outside_evidence": ["..."]
}
```

**Rules**: exactly 7 documents, diverse types/perspectives, proper attribution

## Length Limits

| Field | Min | Max |
|-------|-----|-----|
| MCQ stimulus | 50 | 300 words |
| MCQ question | 10 | 50 words |
| MCQ option | 5 | 40 words |
| MCQ explanation | 50 | 150 words |
| SAQ stimulus | 75 | 250 words |
| SAQ task | 15 | 40 words |
| SAQ sample | 30 | 75 words |
| DBQ document | 100 | 250 words |
| DBQ prompt | 20 | 50 words |
