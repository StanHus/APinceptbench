# Benchmark Run 2 Analysis Report

**Run ID:** `9f5f50a1-b7bc-446b-9011-8ae59e59861a`
**Date:** 2026-02-23
**Endpoint:** `http://192.168.1.10:8000/generate`
**Course:** APUSH

---

## Executive Summary

| Metric | Run 1 | Run 2 | Change |
|--------|-------|-------|--------|
| Total Evaluated | 114 | 117 | +3 |
| **Passed** | 35 (30.7%) | 76 (65.0%) | **+34.3%** |
| **Failed** | 79 (69.3%) | 41 (35.0%) | **-34.3%** |
| Average Score | 0.644 | 0.826 | **+0.182** |

The endpoint update resulted in a **significant improvement**, more than doubling the pass rate from 30.7% to 65.0%.

### Key Improvement: Curriculum Alignment

| Dimension | Run 1 | Run 2 | Change |
|-----------|-------|-------|--------|
| Curriculum Alignment | 43.0% | 88.9% | **+45.9%** |
| Factual Accuracy | 70.2% | 79.5% | +9.3% |
| Cognitive Demand | 64.9% | 66.7% | +1.8% |
| Difficulty Alignment | 84.2% | 86.3% | +2.1% |

The dramatic improvement in curriculum alignment (43% → 89%) confirms the endpoint is now properly utilizing the `learning_objective` and `statement` fields provided in requests.

---

## Remaining Issues

Despite improvements, **41 questions still failed** (35% failure rate). The primary remaining issues are:

1. **Factual Accuracy (79.5% pass)** - Temporal/geographic errors persist
2. **Cognitive Demand (66.7% pass)** - Questions still test recall over analysis
3. **Difficulty Alignment (86.3% pass)** - Hard questions remain too easy
4. **Curriculum Alignment (88.9% pass)** - Some scope creep beyond curriculum

---

## Dimension-by-Dimension Analysis

### 1. Clarity (97.4% pass rate) ✅
Excellent. Questions are well-structured and readable.

### 2. Distractor Quality (96.6% pass rate) ✅
Excellent. Distractors represent plausible misconceptions.

### 3. Explanation Quality (92.3% pass rate) ✅
Good. Explanations are generally comprehensive.

### 4. Curriculum Alignment (88.9% pass rate) ✅
**Major improvement from 43.0%**. The endpoint now properly uses curriculum context.

**Remaining issues (13 failures):**
- Scope expansion beyond provided curriculum (e.g., adding Syria/Libya when curriculum specifies Iraq/Afghanistan only)
- Testing related but different concepts (e.g., urbanization responses vs. immigration responses)
- Topic drift within same general historical period

**Example:**
```
Request: Curriculum about Iraq and Afghanistan withdrawals
Generated: Matching exercise including Syria and Libya
Problem: Expands beyond specified curriculum standard
```

### 5. Difficulty Alignment (86.3% pass rate) ⚠️
**13 failures** - Hard questions are being generated at medium difficulty.

**Pattern:** Matching exercises and fill-in-blanks for "hard" difficulty are too straightforward, lacking the complex analysis required for AP-level hard questions.

**Example:**
```
Requested: Hard difficulty
Generated: Factual matching exercise
Problem: "Medium difficulty factual matching rather than hard-level complex analysis"
```

### 6. Factual Accuracy (79.5% pass rate) ⚠️
**24 failures** - This is now the most common dimension failure.

**Issue patterns:**
1. **Temporal confusion** - Misattributing events to wrong time periods
2. **Geographic errors** - Incorrect regional applications of historical phenomena
3. **Oversimplifications** - Reducing complex historical processes to inaccurate statements

**Examples:**

| Topic | Error |
|-------|-------|
| Immigration (Gilded Age) | Settlement houses framed as Gilded Age (1865-1898) when they were Progressive Era (1890s-1920s) |
| 21st Century Challenges | Claimed U.S. "completed military withdrawal" from Iraq in 2021 (combat mission ended, not full withdrawal) |
| Colonial Period | Encomienda system incorrectly applied to North American Southwest |

### 7. Cognitive Demand (66.7% pass rate) ❌
**22 failures** - This remains the most persistent issue.

**Pattern:** Questions test vocabulary recall instead of the analytical thinking required by learning objectives.

**Examples:**

| Learning Objective | Generated Question | Issue |
|-------------------|-------------------|-------|
| "Explain causes of the Columbian Exchange and its effects" | Fill-in-blank for term "Atlantic World" | Tests vocabulary, not causation |
| "Explain the various responses to immigration over time" | Fill-in-blank for settlement house terminology | Tests memorization, not analysis |
| "Explain causes and effects of domestic challenges" | Basic factual recall | No synthesis or evaluation |

**Root cause:** Fill-in-blank format inherently tests recall. Even with correct curriculum alignment, the question format prevents testing higher-order thinking.

---

## Analysis by Question Format

| Format | Passed | Failed | Pass Rate |
|--------|--------|--------|-----------|
| **MSQ** | 23 | 5 | 82.1% |
| **Fill-in** | 21 | 11 | 65.6% |
| **MCQ** | 14 | 9 | 60.9% |
| **Match** | 18 | 16 | 52.9% |

### Match Format Issues (47.1% failure rate)
Matching exercises are the weakest format:
- Tend toward vocabulary pairing rather than analytical matching
- Hard to achieve appropriate cognitive demand
- Prone to scope expansion

### Fill-in Format Issues (34.4% failure rate)
- Inherently tests recall/recognition
- Difficult to align with "explain how and why" objectives
- Clues often make answers too obvious

### MSQ Format Success (82.1% pass rate)
Multiple-select questions performed best, likely because:
- Format naturally supports testing nuanced understanding
- Requires analysis of multiple factors
- Harder to answer through pure memorization

---

## Analysis by Difficulty Level

| Difficulty | Passed | Failed | Pass Rate |
|------------|--------|--------|-----------|
| **Medium** | 31 | 8 | 79.5% |
| **Easy** | 25 | 13 | 65.8% |
| **Hard** | 20 | 20 | 50.0% |

### Hard Difficulty Problem (50% pass rate)
Half of all "hard" questions failed. The endpoint struggles to generate appropriately challenging content:
- Matching exercises lack complexity
- Questions can be answered with basic recall
- Missing synthesis/evaluation-level demands

---

## Analysis by Topic (Lowest Performers)

| Topic | Pass Rate |
|-------|-----------|
| Movement in the Early Republic | 0.0% (0/3) |
| Responses to Immigration (Gilded Age) | 33.3% (2/6) |
| Cultural Interactions (Colonial) | 33.3% (1/3) |
| Rise of Political Parties | 33.3% (1/3) |
| Colonial Society and Culture | 33.3% (1/3) |
| African Americans (Early Republic) | 33.3% (1/3) |

The "Responses to Immigration" topic had multiple failures due to temporal confusion between Gilded Age and Progressive Era.

---

## Specific Failure Examples

### Example 1: Factual Accuracy Error

**Request:**
```
Topic: Responses to Immigration in the Gilded Age
Difficulty: Medium
Statement: Settlement houses represented an expanding public role for women
           during the Progressive Era...
```

**Problem:** Question frames settlement houses as a Gilded Age phenomenon when the curriculum explicitly states they were Progressive Era (1890s-1920s). The Gilded Age ended around 1898.

### Example 2: Cognitive Demand Failure

**Request:**
```
Topic: Columbian Exchange
Learning Objective: Explain causes and effects of the Columbian Exchange
Difficulty: Easy
```

**Generated:** Fill-in-blank testing term "Atlantic World"

**Problem:** Even an "easy" question should test understanding of causation per the learning objective. This tests only vocabulary memorization.

### Example 3: Curriculum Scope Expansion

**Request:**
```
Topic: Challenges of the 21st Century
Statement: U.S. completed military withdrawals from Iraq and Afghanistan...
```

**Generated:** Matching exercise including Syria and Libya

**Problem:** Curriculum specifies Iraq and Afghanistan only. Adding other countries expands beyond the curriculum standard being tested.

### Example 4: Difficulty Mismatch

**Request:**
```
Topic: Cultural Interactions
Difficulty: Easy
Format: Match
```

**Generated:** Simple recognition-based matching

**Problem:** Matching format made question easier than "easy" level for AP content - requires only recognition, not the recall or basic analysis expected.

---

## Recommendations for Further Improvement

### Priority 1: Cognitive Demand for Fill-in Format
- For "explain" objectives, require causal reasoning in blanks
- Avoid single-word vocabulary blanks
- Consider multi-part fill-ins that test relationships

### Priority 2: Hard Difficulty Questions
- Hard questions must require synthesis or evaluation
- Avoid simple matching for hard difficulty
- Include multi-step reasoning requirements

### Priority 3: Temporal Accuracy
- Cross-reference time periods in curriculum statements
- Validate that question framing matches curriculum era
- Flag when question period differs from statement period

### Priority 4: Strict Curriculum Scope
- Only test content explicitly in the statement
- Avoid "related" concepts not in curriculum
- Geographic and topical constraints must be respected

---

## Comparison Summary

| Aspect | Run 1 | Run 2 | Status |
|--------|-------|-------|--------|
| Curriculum Alignment | 43.0% | 88.9% | ✅ Fixed |
| Factual Accuracy | 70.2% | 79.5% | ⚠️ Improved |
| Cognitive Demand | 64.9% | 66.7% | ❌ Minimal change |
| Difficulty Alignment | 84.2% | 86.3% | ⚠️ Stable |
| Overall Pass Rate | 30.7% | 65.0% | ✅ +34.3% |

---

## Conclusion

The endpoint update successfully addressed the primary Run 1 failure mode (curriculum alignment), resulting in a 34.3% improvement in pass rate.

**Remaining challenges:**
1. **Cognitive demand** remains the most persistent issue - questions test recall instead of analysis
2. **Factual accuracy** errors, particularly temporal/geographic mismatches
3. **Hard difficulty** questions perform poorly (50% pass rate)

The endpoint is now production-viable at 65% pass rate, but further improvements targeting cognitive complexity and temporal accuracy could push pass rates above 80%.
