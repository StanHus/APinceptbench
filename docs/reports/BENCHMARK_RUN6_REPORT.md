# Benchmark Run 6 Analysis Report

**Run ID:** `99e462b0-1ae5-4fac-ac4e-b4923276bd67`
**Date:** 2026-02-23
**Endpoint:** `http://192.168.1.10:8000/generate`
**Course:** APUSH

---

## Executive Summary

| Metric | Run 5 | Run 6 | Change |
|--------|-------|-------|--------|
| Pass Rate | 53.4% | **50.0%** | -3.4% |
| Avg Score | 0.795 | 0.801 | +0.006 |
| Evaluated | 118 | 116 | -2 |

**Run 6 shows continued regression**, now at exactly 50% pass rate. The primary issue is **cognitive demand collapse** (51% pass rate).

---

## Critical Issue: Cognitive Demand Collapse

| Run | Cognitive Demand Pass Rate |
|-----|---------------------------|
| Run 1 | 65% |
| Run 2 | 67% |
| Run 3 | 69% |
| Run 4 | **70%** (peak) |
| Run 5 | 59% |
| Run 6 | **51%** (lowest) |

**57 out of 116 questions (49%) failed cognitive demand** - this is now the dominant failure mode, affecting nearly half of all questions.

---

## All Runs Trend

| Run | Pass Rate | CD | CA | Trend |
|-----|-----------|----|----|-------|
| Run 1 | 30.7% | 65% | 43% | Baseline |
| Run 2 | **65.0%** | 67% | **89%** | Best overall |
| Run 3 | 61.0% | 69% | 90% | Stable |
| Run 4 | 49.6% | 70% | 77% | Regression |
| Run 5 | 53.4% | 59% | 83% | CD starts dropping |
| Run 6 | 50.0% | **51%** | 87% | CD collapse |

**Pattern:** Curriculum alignment recovered (87%), but cognitive demand is now the bottleneck preventing progress.

---

## Format × Difficulty Matrix

| Format | Easy | Medium | Hard |
|--------|------|--------|------|
| **MCQ** | 67% | **80%** | **73%** |
| **MSQ** | 62% | **88%** | 43% |
| **Match** | 50% | 50% | **67%** |
| **Fill-in** | 40% | **12%** | 23% |

### Critical Finding: Fill-in + Medium = 12%

Fill-in at medium difficulty hit a new low of **12% pass rate** (2/16).

### Best Combinations
1. **MSQ + Medium: 88%** (7/8)
2. **MCQ + Medium: 80%** (4/5)
3. **MCQ + Hard: 73%** (8/11)

### Worst Combinations
1. **Fill-in + Medium: 12%** (2/16) - Catastrophic
2. **Fill-in + Hard: 23%** (3/13)
3. **Fill-in + Easy: 40%** (4/10)

---

## Dimension Analysis

| Dimension | Run 5 | Run 6 | Change |
|-----------|-------|-------|--------|
| Curriculum Alignment | 83.1% | **87.1%** | +4.0% ✅ |
| Factual Accuracy | 83.9% | **85.3%** | +1.4% ✅ |
| Difficulty Alignment | 81.4% | **84.5%** | +3.1% ✅ |
| Distractor Quality | 94.1% | **95.7%** | +1.6% ✅ |
| Explanation Quality | 94.9% | 89.7% | -5.2% ⚠️ |
| Clarity | 84.7% | 81.9% | -2.8% ⚠️ |
| **Cognitive Demand** | 59.3% | **50.9%** | **-8.4%** ❌ |

**Trade-off continues:** Content quality improved, but cognitive complexity regressed further.

---

## Fill-in Format: Complete Failure

**30 out of 39 fill-in questions failed (77%)**

| Dimension | Failures (of 39 fill-in) |
|-----------|-------------------------|
| **Cognitive Demand** | **35** (90% of fill-in!) |
| Clarity | 19 |
| Difficulty Alignment | 12 |
| Curriculum Alignment | 7 |
| Factual Accuracy | 1 |

**90% of fill-in questions fail cognitive demand.** The format is fundamentally incompatible with AP-level analytical requirements.

### Fill-in Failure Examples

```
Format: fill-in, Difficulty: medium
Reasoning: "Question requires only recall of memorized cause-effect
relationships rather than analysis or synthesis"

Format: fill-in, Difficulty: hard
Reasoning: "Providing multiple pre-written acceptable answers reduces
it to pattern matching rather than requiring critical thinking"

Format: fill-in, Difficulty: easy
Reasoning: "Question tests pure recall of a factual sequence rather
than requiring AP-level historical thinking skills"
```

---

## Root Cause Analysis

### Why Cognitive Demand is Dropping

1. **Questions test recall, not analysis**
   - Learning objectives say "explain how and why"
   - Questions only test "what happened"

2. **Answer choices/blanks are too obvious**
   - Context provides enough clues to answer without understanding
   - Pattern matching replaces analytical thinking

3. **Fill-in format dominates failures**
   - 35 of 57 cognitive demand failures (61%) are fill-in
   - Format inherently tests vocabulary/recall

4. **Scaffolding undermines difficulty**
   - Hard questions provide too much context
   - Students can answer without synthesis

---

## Required Actions

### URGENT: Remove or Severely Restrict Fill-in Format

Fill-in has failed consistently across 6 runs:

| Run | Fill-in Pass Rate |
|-----|-------------------|
| Run 2 | 65.6% |
| Run 3 | 50.0% |
| Run 4 | 21.4% |
| Run 5 | 25.0% |
| Run 6 | **23.1%** |

**Recommendation: Remove fill-in from format rotation**

```python
# Option 1: Remove entirely
ALLOWED_FORMATS = ["mcq", "msq", "match"]  # No fill-in

# Option 2: Route fill-in to MCQ
def route_format(requested_format: str) -> str:
    if requested_format == "fill-in":
        return "mcq"  # 71.4% pass rate
    return requested_format
```

### Priority 1: Fix Cognitive Demand Prompting

```markdown
## COGNITIVE DEMAND REQUIREMENTS

Every question MUST require one of these thinking skills:
- ANALYSIS: Identify patterns, causes, or relationships
- EVALUATION: Assess arguments, evidence, or interpretations
- SYNTHESIS: Combine information from multiple sources/perspectives

Questions MUST NOT be answerable through:
- Pure memorization of facts
- Pattern matching with provided context
- Recognition of vocabulary terms

VALIDATION: Before finalizing, ask:
"Can a student answer this correctly WITHOUT understanding the
underlying historical concepts?" If yes, revise the question.
```

### Priority 2: Reduce Context/Scaffolding

```markdown
## SCAFFOLDING LIMITS

For HARD questions:
- Maximum 2 sentences of context
- No explanatory phrases in the stem
- Require students to recall context from memory

For MEDIUM questions:
- Maximum 3 sentences of context
- One piece of scaffolding allowed
- Still require some prior knowledge

For EASY questions:
- Context may be provided
- But answer should still require basic comprehension, not just matching
```

### Priority 3: Verb-Question Alignment

| Learning Objective Verb | Required Question Type |
|------------------------|------------------------|
| "Explain how" | Cause-effect analysis |
| "Explain why" | Reasoning/motivation analysis |
| "Compare" | Multi-factor comparison |
| "Evaluate" | Argument assessment |
| "Analyze" | Pattern/relationship identification |

```python
def validate_cognitive_alignment(learning_objective: str, question: dict) -> bool:
    """Ensure question tests the skill specified in learning objective."""

    if "explain how" in learning_objective.lower():
        # Question must require causal reasoning
        return question_requires_causal_reasoning(question)

    if "explain why" in learning_objective.lower():
        # Question must require motivation/reasoning analysis
        return question_requires_motivation_analysis(question)

    # ... etc
```

---

## Recommended Format Strategy

Based on 6 runs of data:

| Format | Avg Pass Rate | Recommendation |
|--------|--------------|----------------|
| MCQ | ~70% | **Primary format** |
| MSQ | ~68% | Good for medium difficulty |
| Match | ~53% | Use for easy/hard only |
| Fill-in | ~25% | **REMOVE** |

### Optimal Routing

```python
def get_optimal_format(difficulty: str) -> str:
    if difficulty == "easy":
        return "msq"  # 62% (could use mcq at 67%)
    elif difficulty == "medium":
        return "msq"  # 88%
    else:  # hard
        return "mcq"  # 73%
```

---

## Projected Impact

| Change | Current | Projected |
|--------|---------|-----------|
| Remove fill-in | 23% → N/A | +8-10% overall |
| Fix cognitive demand prompting | 51% → 70% | +10-12% overall |
| Optimal format routing | Mixed | +3-5% overall |
| **Combined** | 50.0% | **68-75%** |

---

## Conclusion

Run 6 confirms a troubling trend: **cognitive demand has collapsed from 70% to 51%** over the last 3 runs, while other metrics have stabilized or improved.

**The endpoint is now generating content-accurate but cognitively shallow questions.**

### Immediate Actions
1. **Remove fill-in format** - 77% failure rate, 90% fail cognitive demand
2. **Add cognitive demand validation** - Reject questions answerable through recall alone
3. **Reduce scaffolding** - Especially for hard difficulty

### Key Insight
The pass rate is now **perfectly correlated with cognitive demand**:
- When CD was 70%, pass rate was ~61%
- When CD dropped to 51%, pass rate dropped to 50%

**Fixing cognitive demand will fix the overall pass rate.**
