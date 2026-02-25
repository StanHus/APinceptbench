# Benchmark Run 4 Analysis Report

**Run ID:** `b835d6db-13be-4805-9fa7-8f5392b2ad96`
**Date:** 2026-02-23
**Endpoint:** `http://192.168.1.10:8000/generate`
**Course:** APUSH

---

## Executive Summary

| Metric | Run 2 | Run 3 | Run 4 | Trend |
|--------|-------|-------|-------|-------|
| Pass Rate | 65.0% | 61.0% | **49.6%** | ↓↓ |
| Avg Score | 0.826 | 0.827 | 0.755 | ↓ |
| Curriculum Alignment | 88.9% | 89.8% | **77.0%** | ↓↓ |

**Run 4 represents a significant regression.** Pass rate dropped 11.4% from Run 3 and 15.4% from Run 2.

---

## Critical Issue: Format Non-Compliance

**15 out of 26 curriculum alignment failures (58%) are due to FORMAT MISMATCH.**

The endpoint is ignoring requested formats:
- Fill-in requests → returned as MCQ
- Match requests → returned as MSQ

### Impact by Format

| Format | Requested | Pass Rate | Primary Issue |
|--------|-----------|-----------|---------------|
| Fill-in | 28 | **21.4%** | Wrong format returned |
| Match | 25 | 52.0% | Wrong format returned |
| MCQ | 31 | 61.3% | Factual errors |
| MSQ | 29 | 62.1% | Cognitive demand |

### Format × Difficulty Matrix

| Format | Easy | Medium | Hard |
|--------|------|--------|------|
| MCQ | 38% | 67% | 73% |
| MSQ | 40% | 71% | 75% |
| Fill-in | 23% | 43% | **0%** |
| Match | **0%** | 67% | 71% |

**Two catastrophic combinations:**
1. **Fill-in + Hard = 0%** - All 8 questions failed
2. **Match + Easy = 0%** - All 6 questions failed

---

## Root Cause Analysis

### Issue 1: Format Mismatch (NEW in Run 4)

The endpoint update broke format compliance:

```
Request: type="fill-in"
Returned: MCQ-style question with choices A, B, C, D

Evaluator reasoning: "Content delivered as MCQ when fill-in-the-blank
was explicitly requested. Format mismatch is a fundamental curriculum
alignment violation."
```

**This is a regression from Run 3** where format compliance was not an issue.

### Issue 2: Easy Difficulty Collapse (73% failure rate)

| Dimension | Failures (of 37 easy questions) |
|-----------|--------------------------------|
| Cognitive Demand | **26 failures** (70%) |
| Curriculum Alignment | 13 failures |
| Factual Accuracy | 8 failures |
| Difficulty Alignment | 7 failures |

**26 out of 37 easy questions failed cognitive demand** - They are testing at the wrong cognitive level (too complex or wrong skill).

### Issue 3: Fill-in Format Breakdown

Fill-in questions have multiple compounding issues:

| Dimension | Failures (of 28 fill-in) |
|-----------|-------------------------|
| Cognitive Demand | **17 failures** |
| Clarity | **15 failures** |
| Curriculum Alignment | 11 failures |
| Factual Accuracy | 8 failures |

**New clarity failures:** Fill-in blanks are ambiguous about expected answers.

Example:
```
"The range of acceptable answers for blank 1 creates ambiguity
about the expected level of specificity"
```

---

## Dimension Analysis

| Dimension | Run 3 | Run 4 | Change | Status |
|-----------|-------|-------|--------|--------|
| Curriculum Alignment | 89.8% | 77.0% | **-12.8%** | ❌ REGRESSED |
| Factual Accuracy | 81.4% | 75.2% | -6.2% | ⚠️ Regressed |
| Cognitive Demand | 68.6% | 69.9% | +1.3% | → Stable |
| Difficulty Alignment | 83.1% | 90.3% | +7.2% | ✅ Improved |
| Clarity | 94.9% | 85.0% | **-9.9%** | ❌ REGRESSED |
| Distractor Quality | 95.8% | 90.3% | -5.5% | ⚠️ Regressed |
| Explanation Quality | 90.7% | 86.7% | -4.0% | ⚠️ Regressed |

**Three dimensions regressed significantly:**
1. Curriculum alignment (format mismatch)
2. Clarity (ambiguous fill-in blanks)
3. Factual accuracy

---

## Specific Failure Examples

### Example 1: Fill-in → MCQ Format Mismatch

**Request:**
```
Format: fill-in
Topic: Market Revolution: Society and Culture
Difficulty: hard
```

**Failure:**
```
curriculum_alignment: "Content completely fails format requirements -
this is a multiple choice question when fill-in-the-blank was
explicitly requested"

factual_accuracy: "Cannot verify factual accuracy because the actual
answer choices are missing"
```

### Example 2: Match → MSQ Format Mismatch

**Request:**
```
Format: match
Topic: The African American Civil Rights Movement (1960s)
Difficulty: easy
```

**Failure:**
```
curriculum_alignment: "Content covers correct topic but fails format
requirement (MSQ instead of matching)"

difficulty_alignment: "Question requires understanding of Supreme Court
cases... making it moderate difficulty rather than easy"
```

### Example 3: Easy Cognitive Demand Failure

**Request:**
```
Format: match
Topic: Challenges of the 21st Century
Difficulty: easy
```

**Failure:**
```
cognitive_demand: "Question primarily tests factual recall rather than
AP-level analysis. Students can answer by memorizing basic facts
without demonstrating historical thinking skills"
```

### Example 4: Fill-in Clarity Failure

**Request:**
```
Format: fill-in
Topic: World War II: Mobilization
```

**Failure:**
```
clarity: "The question stem is ambiguous and could apply to multiple
wartime policies beyond Japanese internment"
```

---

## Historical Trend

| Run | Pass Rate | CA | CD | FA | Key Issue |
|-----|-----------|----|----|-----|-----------|
| Run 1 | 30.7% | 43% | 65% | 70% | Ignored curriculum context |
| Run 2 | 65.0% | 89% | 67% | 79% | Fixed curriculum alignment |
| Run 3 | 61.0% | 90% | 69% | 81% | Format-difficulty interactions |
| **Run 4** | **49.6%** | **77%** | 70% | 75% | **Format mismatch introduced** |

**Run 4 regressed to worse than Run 2** due to format compliance breakdown.

---

## Required Fixes

### Priority 1: CRITICAL - Fix Format Compliance

The endpoint MUST return the requested format:

```python
# Request validation
if request.type == "fill-in":
    assert response.format == "fill-in"
    assert "___" in response.stem or response.blanks is not None
    assert response.choices is None  # No MCQ choices!

if request.type == "match":
    assert response.format == "match"
    assert response.left_items is not None
    assert response.right_items is not None
    assert response.choices is None  # No MSQ choices!
```

**Implementation:**
1. Add format validation in endpoint
2. If fill-in requested, force fill-in generation template
3. If match requested, force match generation template
4. Reject/retry if format mismatch detected

### Priority 2: Fix Easy Difficulty Questions

Easy questions fail 73% of the time. Two issues:

**Issue A: Too complex for easy**
```
Fix: Add explicit constraints for easy difficulty:
- Maximum 2 factors to consider
- Single cause-effect relationship
- No multi-step reasoning required
- Basic comprehension, not analysis
```

**Issue B: Wrong cognitive level**
```
Fix: Match cognitive demand to difficulty:
- Easy → Remember/Understand (Bloom's 1-2)
- Medium → Apply/Analyze (Bloom's 3-4)
- Hard → Evaluate/Create (Bloom's 5-6)
```

### Priority 3: Fix Fill-in Clarity

Fill-in blanks are ambiguous. Requirements:

```markdown
## Fill-in Clarity Requirements

1. Each blank should have ONE clear correct answer
2. Specify expected granularity (term, phrase, concept)
3. Context must disambiguate the answer
4. Avoid blanks where multiple correct answers exist

Bad: "The _____ policy affected the economy"
Good: "The [specific name] Act of 1890 established [specific provision]"
```

### Priority 4: Routing (Workaround)

Until format compliance is fixed, route away from broken combinations:

```python
def route_format(difficulty: str, requested_format: str) -> str:
    # CRITICAL: These combinations have 0% pass rate
    if requested_format == "fill-in" and difficulty == "hard":
        return "mcq"  # 73% pass rate

    if requested_format == "match" and difficulty == "easy":
        return "msq"  # 40% pass rate (still bad, but not 0%)

    # Fill-in is broken across all difficulties
    if requested_format == "fill-in":
        return "mcq"  # Until fill-in format is fixed

    return requested_format
```

---

## Prompt Engineering Suggestions

### For Format Enforcement

Add explicit format instructions at the START of the prompt:

```markdown
## CRITICAL FORMAT REQUIREMENT

You MUST generate a {format_type} question.

{format_type == "fill-in"}:
- Create sentences with numbered blanks: ___1___, ___2___
- Do NOT include multiple choice options
- Each blank tests a specific concept
- Provide answers as: {"1": "answer1", "2": "answer2"}

{format_type == "match"}:
- Create two columns: LEFT items and RIGHT items
- Students match LEFT to RIGHT
- Do NOT create multiple choice or multiple select
- Provide answer mapping: {"A": "1", "B": "3", ...}

VIOLATION OF FORMAT WILL RESULT IN REJECTION.
```

### For Easy Difficulty

```markdown
## EASY DIFFICULTY CONSTRAINTS

This is an EASY question. You MUST:
- Test ONE simple fact or relationship
- Require NO multi-step reasoning
- Use straightforward vocabulary
- Have obviously wrong distractors (for MCQ)
- Test recall or basic comprehension ONLY

Do NOT:
- Require analysis or synthesis
- Include complex cause-effect chains
- Test nuanced distinctions
- Use sophisticated vocabulary
```

### For Fill-in Clarity

```markdown
## FILL-IN CLARITY REQUIREMENTS

Each blank MUST have exactly ONE correct answer.

Before finalizing, verify:
1. Could a student give a different valid answer? If yes, revise.
2. Is the expected granularity clear? (term vs phrase vs concept)
3. Does context fully constrain the answer?

Example of ambiguous (BAD):
"The _____ led to economic changes"
(Could be: policy, law, act, regulation, tariff, etc.)

Example of clear (GOOD):
"The Sherman Antitrust Act of 1890 targeted _____"
(Only answer: monopolies/trusts)
```

---

## Projected Impact of Fixes

| Fix | Estimated Impact |
|-----|-----------------|
| Format compliance | +10-15% |
| Easy difficulty fix | +5-8% |
| Fill-in clarity | +3-5% |
| Routing (interim) | +5-7% |
| **Combined** | **+15-25%** |

With fixes, projected pass rate: **65-75%** (back to Run 2-3 levels)

---

## Conclusion

**Run 4 is a regression caused by format non-compliance.**

The endpoint update broke the ability to generate fill-in and match formats correctly, instead returning MCQ/MSQ formats regardless of request.

**Immediate action required:**
1. Revert to Run 3 endpoint behavior if possible
2. Or implement format validation/enforcement
3. Add routing as temporary workaround

**The core curriculum alignment capability from Run 2-3 appears intact** - the 77% curriculum alignment is dragged down by format mismatch, not content issues. Once format compliance is restored, pass rates should return to 60-65% range, with potential for further improvement through difficulty and clarity fixes.
