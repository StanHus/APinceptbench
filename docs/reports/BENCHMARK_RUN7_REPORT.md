# Benchmark Run 7 Analysis Report

**Run ID:** `7084f6e5-4431-4998-a49c-1236af5989c9`
**Date:** 2026-02-24
**Endpoint:** `http://192.168.1.10:8000/generate`
**Course:** APUSH

---

## Summary

| Metric | Value |
|--------|-------|
| Total Evaluated | 116 |
| Passed | 73 |
| Failed | 43 |
| Pass Rate | 62.9% |

---

## Format × Difficulty Failures

| Format | Easy | Medium | Hard | Total |
|--------|------|--------|------|-------|
| **fill-in** | 43% (3/7) | 57% (4/7) | 67% (4/6) | **55%** (11/20) |
| **match** | 50% (3/6) | 56% (5/9) | 50% (9/18) | **52%** (17/33) |
| **mcq** | 43% (6/14) | 9% (1/11) | 22% (2/9) | **26%** (9/34) |
| **msq** | 23% (3/13) | 17% (2/12) | 25% (1/4) | **21%** (6/29) |
| **Overall** | **38%** (15/40) | **31%** (12/39) | **43%** (16/37) | **37%** (43/116) |

---

## Dimension Failure Counts

| Dimension | Failures | % of Failed Questions |
|-----------|----------|----------------------|
| factual_accuracy | 20 | 47% |
| cognitive_demand | 20 | 47% |
| curriculum_alignment | 17 | 40% |
| difficulty_alignment | 11 | 26% |
| explanation_quality | 10 | 23% |
| clarity | 5 | 12% |
| distractor_quality | 4 | 9% |

---

## Failure Analysis by Format

### Fill-in: 55% failure rate (11/20)

Top failure dimensions:
- cognitive_demand: Questions test recall rather than analysis
- curriculum_alignment: Content doesn't match learning objectives

### Match: 52% failure rate (17/33)

Top failure dimensions:
- difficulty_alignment: 1:1 matching without distractors reduces difficulty
- distractor_quality: No extra options to create analytical challenge

### MCQ: 26% failure rate (9/34)

Top failure dimensions:
- factual_accuracy: Historical facts or time periods incorrect
- cognitive_demand: Questions answerable through pattern matching

### MSQ: 21% failure rate (6/29)

Top failure dimensions:
- curriculum_alignment: Content outside specified time period
- explanation_quality: Superficial explanations

---

## Sample Failure Reasons

### Factual Accuracy Failures (20 questions)

```
"Contains a factual error regarding the name of the legislation
that created Medicare and Medicaid"

"Factual error regarding time period - the curriculum specifies
1877-1900, but explanation references 1865-1877"

"Incorrect attribution of historical event to wrong decade"
```

### Cognitive Demand Failures (20 questions)

```
"Question requires only basic recall of information directly
provided in curriculum materials without requiring analysis"

"While the question requires understanding consequences, the
redundant terms reduce the analytical challenge significantly"

"This is primarily a recall question asking students to identify
factual statements rather than requiring analytical thinking"
```

### Curriculum Alignment Failures (17 questions)

```
"Content tests the correct topic but focuses on the wrong time
period. The curriculum specifies 1877-1900 but content examines
Reconstruction policies from 1865-1877"

"Question tests generic knowledge about legislative power shifts
but doesn't address the specific learning objective"

"Content fails to test the specific learning objective about
policy debates regarding federal government role over time"
```

### Difficulty Alignment Failures (11 questions)

```
"The 1:1 matching format with no distractors makes this more
of a medium difficulty question despite being marked as hard"

"The actual difficulty is lower than the requested 'hard' level
due to structural issues that make the question easier to solve"
```

---

## Failure Distribution

| Failure Type | Count |
|--------------|-------|
| Single dimension failure | 12 |
| 2 dimension failures | 14 |
| 3+ dimension failures | 17 |

---

## Archive

Full failure details exported to: `latest_run_failures.json` (100KB)

Contains for each failed question:
- Question stem and options
- Learning objective tested
- All failed dimensions with reasoning
- Specific issues identified
