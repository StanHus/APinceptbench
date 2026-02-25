# Benchmark Failure Analysis Report

**Run ID:** `3de8a1ae-4f24-4996-a245-d7c92a9daa4b`
**Date:** 2026-02-23
**Endpoint:** `http://192.168.1.10:8000/generate`
**Course:** APUSH

---

## Executive Summary

| Metric | Value |
|--------|-------|
| Total Generated | 120 |
| Total Evaluated | 114 |
| **Passed** | 35 (30.7%) |
| **Failed** | 79 (69.3%) |
| Average Score | 0.644 |

The endpoint failed to produce acceptable questions in **nearly 70% of cases**. The primary failure modes are:

1. **Curriculum Alignment (43% pass rate)** - Questions frequently miss the specific curriculum focus
2. **Factual Accuracy (70% pass rate)** - Oversimplifications and minor errors
3. **Cognitive Demand (65% pass rate)** - Questions test recall instead of analysis

---

## Critical Finding: Curriculum Alignment Failures

**65 out of 79 failed questions** had curriculum alignment issues. This is the **dominant failure mode**.

### Root Cause
The generator ignores the specific `learning_objective` and `statement` provided in the request. Instead, it produces generic questions about the broad topic area.

### Example Pattern

**Request:**
- Topic: "Reconstruction"
- Learning Objective: "Explain the effects of government policy during Reconstruction"
- Curriculum Statement: "The Fifteenth Amendment, ratified in 1870, prohibited denying voting rights..."

**Generated:** Question about land policy and sharecropping

**Expected:** Question about the 15th Amendment and voting rights

### Impact by Topic
The "An Age of Reform" topic had particularly severe issues:
- Curriculum specifies: Sojourner Truth, Grimké sisters, intersection of race and gender
- Generator produced: Generic matching of reform movements to issues
- Result: Complete curriculum mismatch

---

## Failure Analysis by Question Format

| Format | Fail Rate | Primary Issues |
|--------|-----------|----------------|
| **MCQ** | 77.4% | Curriculum alignment (19), Factual accuracy (15) |
| **Fill-in** | 75.9% | Curriculum alignment (20), Cognitive demand (15) |
| **MSQ** | 66.7% | Curriculum alignment (16), Factual accuracy (8) |
| **Match** | 55.6% | Cognitive demand (11), Curriculum alignment (10) |

### MCQ Issues
- Questions often contain factual errors in answer choices
- Distractors occasionally include implausible options
- Questions test broad topic knowledge instead of specific curriculum points

### Fill-in Issues
- Blanks test vocabulary/terminology recall
- Missing connection to analytical learning objectives
- Often tests wrong time period or concept

### Match Issues
- Degenerates into "vocabulary matching"
- Tests recall instead of analysis
- Difficulty levels ignored (hard questions are actually easy)

---

## Failure Analysis by Difficulty Level

| Difficulty | Pass Rate |
|------------|-----------|
| Easy | 29.7% |
| Medium | 35.9% |
| Hard | 26.3% |

### Hard Difficulty Failures
The generator struggles most with "hard" questions:
- Matching exercises are inappropriately simple
- Questions test factual recall instead of complex analysis
- No synthesis or evaluation-level cognitive demand

**Example:**
- Requested: Hard-level analysis question
- Generated: Basic vocabulary matching exercise
- Evaluator note: "This matching exercise is more appropriate for medium difficulty as it primarily tests knowledge rather than evaluation"

---

## Dimension-by-Dimension Analysis

### 1. Clarity (99.1% pass rate) ✅
The generator produces well-structured, readable questions.

### 2. Explanation Quality (96.5% pass rate) ✅
Explanations for correct/incorrect answers are generally comprehensive.

### 3. Distractor Quality (93.9% pass rate) ✅
Most distractors represent plausible student misconceptions.

### 4. Difficulty Alignment (84.2% pass rate) ⚠️
Questions occasionally mismatch requested difficulty levels, particularly for "hard" questions that become too easy.

### 5. Factual Accuracy (70.2% pass rate) ⚠️
**34 questions contained factual issues:**
- Oversimplifications of historical events
- Incorrect characterizations of cause/effect relationships
- Minor factual errors in answer explanations
- Anachronistic statements

**Examples:**
- "Abolitionist movement demanded immediate and total end to slavery in the 1830s" (oversimplification)
- "Federal expansion complicated Reconstruction goals" (inaccurate primary cause)
- "Northwest Ordinance relationship to African American petitions" (factual error)

### 6. Cognitive Demand (64.9% pass rate) ❌
**33 questions failed cognitive demand:**
- Questions test recall/recognition instead of analysis
- Matching exercises are vocabulary-level
- Fill-in-blanks test terminology, not understanding
- Learning objectives require "explain how and why" but questions only test "what"

### 7. Curriculum Alignment (43.0% pass rate) ❌❌
**65 questions failed curriculum alignment:**
- Complete topic mismatch with provided curriculum facts
- Ignores specific figures/events mentioned in learning objectives
- Tests broad time periods instead of specific curriculum focus
- Misses key analytical requirements

---

## Top Issue Patterns

| Issue ID | Occurrences | Pattern |
|----------|-------------|---------|
| ISSUE1 | 79 | Curriculum/factual mismatch with provided context |
| ISSUE2 | 74 | Recall-level questions instead of analysis |
| ISSUE3 | 44 | Basic matching instead of analytical tasks |
| ISSUE4 | 10 | Tests period names instead of understanding |

---

## Specific Failure Examples

### Example 1: Curriculum Mismatch

**Request:**
```
Topic: An Age of Reform
Learning Objective: Explain how and why various reform movements developed
Curriculum Focus: Sojourner Truth and Grimké sisters, intersection of race/gender
```

**Generated:** Generic matching of reform movements to societal issues

**Problem:** Completely ignores the specific curriculum focus on intersectional analysis of race and gender in reform movements.

### Example 2: Cognitive Demand Failure

**Request:**
```
Topic: Reconstruction
Difficulty: Hard
Learning Objective: Explain the effects of government policy on society
```

**Generated:** Basic factual recall about what amendments said

**Problem:** A "hard" question should require synthesis and evaluation. This question can be answered through memorization.

### Example 3: Factual Error

**Request:**
```
Topic: African Americans in the Early Republic
Format: MCQ
```

**Generated:** Contains error about Northwest Ordinance relationship to African American petitions

**Problem:** Factual inaccuracy undermines educational value.

---

## Recommendations for Endpoint Improvement

### Priority 1: Use Provided Curriculum Context
- The endpoint receives `learning_objective` and `statement` fields
- These should directly inform question content
- Questions must test the specific curriculum point, not the general topic

### Priority 2: Increase Cognitive Complexity
- Move beyond recall/recognition to analysis/evaluation
- For "explain how and why" objectives, require causal reasoning
- Matching should require analysis, not just vocabulary pairing

### Priority 3: Difficulty Calibration
- "Hard" questions must require complex analysis
- "Easy" questions should still align with curriculum focus
- Difficulty should affect cognitive demand, not just vocabulary

### Priority 4: Fact-Check Generated Content
- Implement validation for historical claims
- Avoid oversimplifications of complex events
- Ensure consistency between question content and explanations

---

## Passing Question Characteristics

Questions that passed tended to:
1. Directly address the specific curriculum point provided
2. Test analytical skills appropriate to AP level
3. Include historically accurate content
4. Match the requested difficulty level
5. Use distractors representing real student misconceptions

---

## Conclusion

The 69.3% failure rate is primarily driven by **curriculum alignment** and **cognitive demand** issues. The generator appears to:

1. Ignore the specific curriculum context provided in requests
2. Default to recall-level questions regardless of difficulty
3. Produce generic topic-area questions instead of targeted curriculum assessments

The endpoint needs significant improvement in utilizing the provided `learning_objective` and `statement` fields to generate appropriately focused and analytically demanding questions.
