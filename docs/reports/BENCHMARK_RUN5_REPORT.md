# Benchmark Run 5 Analysis Report

**Run ID:** `73ced3ed-1cc6-4f34-8d82-7a948976c847`
**Date:** 2026-02-23
**Endpoint:** `http://192.168.1.10:8000/generate`
**Course:** APUSH

---

## Executive Summary

| Metric | Run 4 | Run 5 | Change |
|--------|-------|-------|--------|
| Pass Rate | 49.6% | **53.4%** | +3.8% |
| Avg Score | 0.755 | 0.795 | +0.040 |
| Evaluated | 113 | 118 | +5 |

**Slight improvement from Run 4**, but significant pattern shift in difficulty performance.

---

## All Runs Comparison

| Run | Pass Rate | Easy | Medium | Hard | CA | CD |
|-----|-----------|------|--------|------|----|----|
| Run 1 | 30.7% | 30% | 36% | 26% | 43% | 65% |
| Run 2 | **65.0%** | 66% | **79%** | 50% | **89%** | 67% |
| Run 3 | 61.0% | 46% | 68% | **69%** | 90% | 69% |
| Run 4 | 49.6% | 27% | 63% | 58% | 77% | **70%** |
| **Run 5** | 53.4% | **68%** | 54% | 38% | 83% | 59% |

**Key observation:** Run 5 fixed easy difficulty (27% → 68%) but broke hard difficulty (58% → 38%) and cognitive demand (70% → 59%).

---

## Critical Issue: Difficulty Inversion

Run 5 shows an **inverted difficulty pattern**:

| Difficulty | Run 4 | Run 5 | Expected |
|------------|-------|-------|----------|
| Easy | 27% | **68%** | Higher pass rate ✓ |
| Medium | 63% | 54% | Medium pass rate ✗ |
| Hard | 58% | **38%** | Lower pass rate ✗ |

**Problem:** Hard questions now fail MORE than easy questions. This suggests:
1. Hard questions are too easy (difficulty_alignment failures)
2. OR hard questions have excessive scaffolding (cognitive_demand failures)

---

## Format × Difficulty Matrix

| Format | Easy | Medium | Hard |
|--------|------|--------|------|
| **MSQ** | **92%** | 78% | 40% |
| **MCQ** | 67% | **83%** | 64% |
| **Match** | 64% | 55% | 38% |
| **Fill-in** | 38% | 23% | **20%** |

### Best Combinations
1. **MSQ + Easy: 92%** (11/12) - Excellent
2. **MCQ + Medium: 83%** (5/6) - Strong
3. **MSQ + Medium: 78%** (7/9) - Good

### Worst Combinations
1. **Fill-in + Hard: 20%** (3/15) - Still catastrophic
2. **Fill-in + Medium: 23%** (3/13) - Very poor
3. **Match + Hard: 38%** (3/8) - Poor
4. **MSQ + Hard: 40%** (2/5) - Poor

---

## Dimension Analysis

| Dimension | Run 4 | Run 5 | Change | Status |
|-----------|-------|-------|--------|--------|
| Factual Accuracy | 75.2% | **83.9%** | +8.7% | ✅ Improved |
| Curriculum Alignment | 77.0% | **83.1%** | +6.1% | ✅ Improved |
| Explanation Quality | 86.7% | **94.9%** | +8.2% | ✅ Improved |
| Distractor Quality | 90.3% | **94.1%** | +3.8% | ✅ Improved |
| Clarity | 85.0% | 84.7% | -0.3% | → Stable |
| Difficulty Alignment | **90.3%** | 81.4% | **-8.9%** | ❌ Regressed |
| Cognitive Demand | **69.9%** | 59.3% | **-10.6%** | ❌ Regressed |

**Trade-off:** Run 5 improved factual accuracy and curriculum alignment but regressed on difficulty alignment and cognitive demand.

---

## Root Cause: Hard Difficulty Failures

**24 out of 39 hard questions failed (62%)**

| Failure Dimension | Count |
|-------------------|-------|
| Difficulty Alignment | **17** |
| Cognitive Demand | 10 |
| Curriculum Alignment | 8 |
| Factual Accuracy | 8 |

### Primary Issue: Questions Too Easy

Hard questions are being generated at medium or easy cognitive levels:

```
Evaluator: "While the question addresses complex concepts, the overly
detailed answer choices and extensive scaffolding reduce this to a
matching exercise rather than requiring analytical thinking"

Evaluator: "Question fails to meet AP-level cognitive demand due to
excessive scaffolding that makes the answers predictable"
```

**Pattern:** The endpoint adds too much context/scaffolding, which paradoxically makes hard questions easier to answer.

---

## Fill-in Format: Persistent Failure

**27 out of 36 fill-in questions failed (75%)**

| Dimension | Failures |
|-----------|----------|
| Cognitive Demand | **26** |
| Difficulty Alignment | 16 |
| Clarity | 16 |
| Curriculum Alignment | 11 |

Fill-in remains the most problematic format across ALL runs:

| Run | Fill-in Pass Rate |
|-----|-------------------|
| Run 2 | 65.6% |
| Run 3 | 50.0% |
| Run 4 | 21.4% |
| Run 5 | **25.0%** |

### Fill-in Issues

1. **Cognitive demand (26 failures):** Blanks test vocabulary, not analysis
2. **Difficulty alignment (16 failures):** Easy/hard questions feel the same
3. **Clarity (16 failures):** Ambiguous what answer is expected

---

## Improvements Needed

### Priority 1: Fix Hard Difficulty (38% → target 60%+)

**Problem:** Excessive scaffolding makes hard questions too easy.

**Solution - Reduce Context for Hard:**
```markdown
## HARD DIFFICULTY REQUIREMENTS

For HARD questions, you MUST:
- Provide MINIMAL context in the stem
- Require students to RECALL and SYNTHESIZE information
- NOT include hints or leading phrases
- Require evaluation of competing interpretations
- Test nuanced distinctions between similar concepts

AVOID:
- Detailed explanations in the question stem
- Answer choices that telegraph the correct answer
- Scaffolding that guides students to the answer
```

**Implementation:**
```python
def adjust_prompt_for_difficulty(difficulty: str, base_prompt: str) -> str:
    if difficulty == "hard":
        return base_prompt + """

HARD MODE: Remove all scaffolding. The question should require:
- Prior knowledge recall (not provided in stem)
- Multi-step reasoning
- Evaluation of competing claims
- Synthesis across multiple concepts

Do NOT include explanatory context that makes the answer obvious.
"""
    return base_prompt
```

### Priority 2: Fix Cognitive Demand (59% → target 75%+)

**Problem:** Questions test recall instead of analysis.

**Solution - Cognitive Verb Alignment:**
```markdown
## COGNITIVE DEMAND MATRIX

| Learning Objective Verb | Required Question Type |
|------------------------|------------------------|
| "Explain how and why" | Cause-effect analysis |
| "Compare and contrast" | Multi-factor comparison |
| "Evaluate" | Argument assessment |
| "Analyze" | Pattern identification |

If the learning objective says "explain," the question MUST require
explanation, not just identification or recall.
```

### Priority 3: Fix or Remove Fill-in Format

Fill-in has failed consistently across 4 runs. Options:

**Option A: Remove fill-in entirely**
```python
ALLOWED_FORMATS = ["mcq", "msq", "match"]  # Remove fill-in
```

**Option B: Restrict fill-in to specific cases**
```python
def can_use_fill_in(learning_objective: str, difficulty: str) -> bool:
    # Only use fill-in for identification objectives, not analysis
    if "explain" in learning_objective.lower():
        return False
    if "analyze" in learning_objective.lower():
        return False
    if difficulty == "hard":
        return False
    return True
```

**Option C: Complete fill-in redesign**
```markdown
## FILL-IN REDESIGN

Instead of single-word blanks, use RELATIONSHIP blanks:

Bad: "The _____ Act was passed in 1890"
Good: "The Sherman Antitrust Act addressed [economic problem]
       by [mechanism], which resulted in [consequence]"

Each blank should test UNDERSTANDING, not VOCABULARY.
```

### Priority 4: Format Routing

Based on Run 5 data, implement routing:

```python
def optimal_format(difficulty: str, learning_objective: str) -> str:
    """Route to best format based on difficulty."""

    # Fill-in is broken - avoid entirely
    # if requested_format == "fill-in":
    #     return "mcq"

    if difficulty == "easy":
        return "msq"  # 92% pass rate

    if difficulty == "medium":
        return "mcq"  # 83% pass rate

    if difficulty == "hard":
        return "mcq"  # 64% pass rate (best for hard)

    return "mcq"  # Safe default
```

---

## Specific Recommendations

### For Endpoint Developer

1. **Reduce scaffolding for hard questions**
   - Don't explain concepts in the stem
   - Don't include context that makes answers obvious
   - Require students to bring prior knowledge

2. **Match cognitive demand to learning objectives**
   - "Explain why" → require causal reasoning
   - "Analyze" → require pattern identification
   - Don't default to recall-level questions

3. **Fix or disable fill-in format**
   - Current implementation tests vocabulary, not understanding
   - Either redesign completely or remove from rotation

4. **Validate difficulty alignment**
   - Hard questions should require synthesis/evaluation
   - Easy questions should require recall/comprehension
   - Medium questions should require application/analysis

### Routing Table (Interim Fix)

| Difficulty | Recommended Format | Avoid |
|------------|-------------------|-------|
| Easy | MSQ (92%) | Fill-in (38%) |
| Medium | MCQ (83%) | Fill-in (23%) |
| Hard | MCQ (64%) | Fill-in (20%), MSQ (40%) |

---

## Projected Impact

| Fix | Current | Target | Impact |
|-----|---------|--------|--------|
| Hard difficulty fix | 38% | 60% | +8% overall |
| Cognitive demand fix | 59% | 75% | +7% overall |
| Remove fill-in | 25% → N/A | N/A | +5% overall |
| Format routing | - | - | +3% overall |
| **Combined** | 53.4% | **70-75%** | **+17-22%** |

---

## Conclusion

Run 5 shows improvement in factual accuracy (+8.7%) and curriculum alignment (+6.1%) but introduced new problems:

1. **Hard difficulty broken** - 38% pass rate due to excessive scaffolding
2. **Cognitive demand regressed** - 59% (down from 70%)
3. **Fill-in still catastrophic** - 25% pass rate

**The endpoint is now better at content accuracy but worse at difficulty calibration.**

**Immediate actions:**
1. Reduce scaffolding in hard questions
2. Route away from fill-in format
3. Add cognitive demand validation

**Best current combination:** MSQ + Easy (92% pass rate)
**Worst current combination:** Fill-in + Hard (20% pass rate)
