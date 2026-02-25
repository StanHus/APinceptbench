# Benchmark Run 3 Analysis Report

**Run ID:** `3d7ab8e7-170e-4a2e-83e3-b859fe8ef102`
**Date:** 2026-02-23
**Endpoint:** `http://192.168.1.10:8000/generate`
**Course:** APUSH

---

## Executive Summary

| Metric | Run 1 | Run 2 | Run 3 | Trend |
|--------|-------|-------|-------|-------|
| Pass Rate | 30.7% | 65.0% | 61.0% | ↓ 4% |
| Avg Score | 0.644 | 0.826 | 0.827 | → stable |
| Evaluated | 114 | 117 | 118 | → stable |

Run 3 shows a **slight regression** in overall pass rate but reveals critical insights about **format-difficulty interactions** that can be addressed through routing and prompt engineering.

---

## Critical Finding: Format × Difficulty Interactions

The most actionable insight from Run 3 is the dramatic variation in pass rates across format-difficulty combinations:

| Format | Easy | Medium | Hard |
|--------|------|--------|------|
| **MCQ** | 56% | 83% | **88%** |
| **MSQ** | 78% | 54% | 83% |
| **Fill-in** | 50% | 50% | 50% |
| **Match** | **15%** | 73% | 56% |

### Key Observations

1. **Match + Easy = 15%** - Catastrophic failure rate
2. **MCQ + Hard = 88%** - Best performing combination
3. **Fill-in = 50% across all difficulties** - Format-inherent problem
4. **MSQ shows U-shape** - Good at extremes, weak in middle

---

## Dimension Failures by Format

| Format | Factual | Curriculum | Cognitive | Difficulty |
|--------|---------|------------|-----------|------------|
| MCQ | 5 | 3 | 4 | 0 |
| MSQ | 6 | 5 | 7 | 2 |
| Fill-in | 5 | 2 | **13** | **9** |
| Match | 6 | 2 | **13** | **9** |

**Fill-in and Match have identical failure patterns:** massive cognitive demand (13 each) and difficulty alignment (9 each) failures.

---

## Root Cause Analysis

### Match + Easy Failures (15% pass rate)

The matching format at easy difficulty creates a fundamental conflict:
- Easy questions should test basic comprehension
- Matching inherently becomes "vocabulary pairing"
- Learning objectives require "explain how and why"
- Result: Questions are either too simple (cognitive fail) or too complex (difficulty fail)

**Example failures:**
```
Topic: Reagan and Conservatism
Learning Objective: Explain causes and effects of policy debates
Generated: Policy-effect vocabulary matching
Failed: cognitive_demand (memorization, not analysis)
        difficulty_alignment (concepts too sophisticated for "easy")
```

### Fill-in Consistent 50% (All Difficulties)

Fill-in-the-blank has an inherent limitation:
- Format encourages single-word/term answers
- Tests recall regardless of difficulty setting
- Cannot test "explain" or "analyze" verbs
- Difficulty adjustment only changes vocabulary complexity, not cognitive demand

**Easy fill-in:** Often overshoots complexity
**Hard fill-in:** Often undershoots - just memorization with fancy context

### MCQ + Hard Success (88% pass rate)

MCQ format excels at hard difficulty because:
- Complex scenarios can be embedded in stem
- Answer choices can require synthesis/evaluation
- Distractors can test nuanced understanding
- Format supports multi-factor analysis

---

## Recommendations: Routing Strategy

### Recommended Format Routing Matrix

| Difficulty | Primary Format | Secondary | Avoid |
|------------|---------------|-----------|-------|
| **Easy** | MSQ (78%) | MCQ (56%) | Match (15%) |
| **Medium** | MCQ (83%) | Match (73%) | MSQ (54%) |
| **Hard** | MCQ (88%) | MSQ (83%) | Fill-in (50%) |

### Implementation: Format Router

```python
def route_format(difficulty: str, requested_format: str) -> str:
    """Route away from problematic format-difficulty combinations."""

    # Critical: Never use match for easy
    if difficulty == "easy" and requested_format == "match":
        return "msq"  # Redirect to best easy format

    # Avoid fill-in for hard (wastes hard difficulty on recall)
    if difficulty == "hard" and requested_format == "fill-in":
        return "mcq"  # Redirect to best hard format

    # MSQ struggles at medium
    if difficulty == "medium" and requested_format == "msq":
        return "mcq"  # Redirect to best medium format

    return requested_format  # Keep original
```

### Routing Impact Estimate

If routing had been applied to Run 3:
- 13 easy+match questions → routed to MSQ (15% → ~78%)
- Estimated prevented failures: ~8 questions
- Projected pass rate: ~68% (+7%)

---

## Recommendations: Prompt Engineering

### Problem: Generic Prompts Across Formats

Current approach uses similar prompts regardless of format, leading to:
- Fill-in defaulting to vocabulary blanks
- Match defaulting to term pairing
- Easy questions overshooting complexity
- Hard questions undershooting cognitive demand

### Solution: Format-Specific Prompt Templates

#### For Fill-in Format

**Current behavior:** Single-word vocabulary blanks
**Desired behavior:** Relationship/causation blanks

```markdown
## Fill-in Specific Instructions

CRITICAL: Do NOT create vocabulary fill-in-blanks. Instead:

- Blanks should test RELATIONSHIPS, not terms
- Good: "The [economic policy] led to [consequence] because [causal mechanism]"
- Bad: "The _____ was signed in 1787"

For "explain" objectives:
- Create multi-blank sentences testing cause-effect chains
- Require students to demonstrate understanding of WHY, not just WHAT

Example transformation:
- Bad: "The _____ Proclamation freed slaves in Confederate states"
- Good: "Lincoln's Emancipation Proclamation achieved [military objective] by [mechanism], which [political effect]"
```

#### For Match Format

**Current behavior:** Term-to-definition matching
**Desired behavior:** Analytical matching

```markdown
## Match Specific Instructions

CRITICAL: Avoid vocabulary-style matching. Instead:

For EASY difficulty:
- Match causes to effects (not terms to definitions)
- Match events to consequences
- Match policies to outcomes

For HARD difficulty:
- Match complex scenarios to analytical conclusions
- Match historical arguments to their evidence
- Match perspectives to their implications

Example transformation:
- Bad: Match [Term] → [Definition]
- Good: Match [Historical Action] → [Its Primary Consequence]

Never create matching where items can be paired through vocabulary recognition alone.
```

#### For Difficulty-Specific Cognitive Demands

```markdown
## Difficulty-Specific Instructions

### EASY Difficulty
- Test: Basic cause-effect relationships
- Cognitive level: Comprehension (understand, explain simply)
- Avoid: Complex multi-factor analysis
- Avoid: Sophisticated vocabulary that increases difficulty artificially

### MEDIUM Difficulty
- Test: Application of historical patterns
- Cognitive level: Application (apply, compare, contrast)
- Include: 2-3 factors to consider
- Require: Connecting specific events to broader patterns

### HARD Difficulty
- Test: Synthesis and evaluation
- Cognitive level: Analysis/Evaluation (analyze, evaluate, assess)
- Require: Weighing multiple perspectives
- Require: Considering counterarguments or limitations
- Include: Nuanced distinctions between similar concepts
```

---

## Implementation: Prompt Router

```python
def get_format_prompt_additions(format_type: str, difficulty: str) -> str:
    """Return format-specific prompt additions."""

    prompts = {
        "fill-in": {
            "base": """
FILL-IN REQUIREMENTS:
- Create blanks for RELATIONSHIPS and CAUSATION, not vocabulary
- Each blank should test understanding of WHY or HOW
- Avoid single-term blanks that test only recall
""",
            "easy": "- Keep cause-effect chains simple (A causes B)\n",
            "hard": "- Require multi-step causal reasoning (A causes B which leads to C)\n"
        },

        "match": {
            "base": """
MATCHING REQUIREMENTS:
- Match CAUSES to EFFECTS or ACTIONS to CONSEQUENCES
- Never match terms to definitions
- Each match should require historical thinking, not vocabulary recall
""",
            "easy": "- Use clear, direct cause-effect pairs\n- Limit to 4 matches\n",
            "hard": "- Include nuanced distinctions\n- Require evaluation of relative importance\n"
        },

        "mcq": {
            "base": "",  # MCQ performs well with default prompts
            "hard": """
MCQ HARD REQUIREMENTS:
- Stem should present a complex scenario or historical debate
- All options should be historically plausible
- Correct answer requires synthesis of multiple factors
"""
        },

        "msq": {
            "base": "",
            "medium": """
MSQ MEDIUM REQUIREMENTS:
- Ensure clear analytical criteria for selection
- Avoid options that are obviously correct/incorrect
- Require understanding of degree and nuance
"""
        }
    }

    format_prompts = prompts.get(format_type, {})
    result = format_prompts.get("base", "")
    result += format_prompts.get(difficulty, "")
    return result
```

---

## Comparison: Runs 1-3

| Dimension | Run 1 | Run 2 | Run 3 |
|-----------|-------|-------|-------|
| Curriculum Alignment | 43.0% | 88.9% | 89.8% |
| Factual Accuracy | 70.2% | 79.5% | 81.4% |
| Cognitive Demand | 64.9% | 66.7% | 68.6% |
| Difficulty Alignment | 84.2% | 86.3% | 83.1% |
| Distractor Quality | - | 96.6% | 95.8% |
| Explanation Quality | - | 92.3% | 90.7% |
| Clarity | - | 97.4% | 94.9% |

**Curriculum alignment is stable at ~89%** - the fix from Run 1→2 is holding.

**Cognitive demand remains the bottleneck** at 68.6% - requires format-specific prompting.

---

## Specific Failure Examples

### Example 1: Match + Easy Catastrophe

**Request:**
```
Format: match
Difficulty: easy
Topic: Reagan and Conservatism
Learning Objective: Explain causes and effects of policy debates
```

**Generated:** Policy-effect vocabulary matching

**Failed dimensions:**
- cognitive_demand: "Tests memorization of policy-effect relationships rather than requiring analysis"
- difficulty_alignment: "Complex definitions make this harder than 'easy' level"

**Fix:** Route to MSQ, or use cause-effect matching prompt

### Example 2: Fill-in Cognitive Ceiling

**Request:**
```
Format: fill-in
Difficulty: hard
Topic: Government Policies During the Civil War
Learning Objective: Explain how Lincoln's leadership impacted American ideals
```

**Generated:** Fill-in-blank about greenbacks

**Failed:** cognitive_demand: "Requires factual recall rather than analysis of leadership impact"

**Fix:** Multi-blank causation template, or route to MCQ for hard difficulty

### Example 3: Easy Difficulty Overshoot

**Request:**
```
Format: fill-in
Difficulty: easy
Topic: Manifest Destiny
Learning Objective: Explain causes and effects of westward expansion
```

**Failed:** cognitive_demand: "Requires sophisticated analysis of ideological contradictions, exceeding basic comprehension level"

**Fix:** Easy-specific prompt limiting complexity

---

## Action Items

### Immediate (Routing)

1. **Block match + easy combination** - Route to MSQ
2. **Block fill-in + hard combination** - Route to MCQ
3. **Consider blocking msq + medium** - Route to MCQ

### Short-term (Prompting)

4. **Add format-specific prompt sections** for fill-in and match
5. **Add difficulty-specific cognitive demand guidelines**
6. **Enforce "no vocabulary matching" rule for match format**

### Medium-term (Structural)

7. **Consider removing fill-in format** for "explain" learning objectives
8. **Create separate prompt templates** per format-difficulty combination
9. **Add pre-generation validation** to catch format-objective mismatches

---

## Projected Impact

| Change | Estimated Impact |
|--------|-----------------|
| Route match+easy → MSQ | +5-7% pass rate |
| Route fill-in+hard → MCQ | +2-3% pass rate |
| Format-specific prompts | +3-5% pass rate |
| **Combined** | **+10-15% pass rate** |

With routing and prompt changes, projected pass rate: **71-76%**

---

## Conclusion

Run 3 reveals that **format-difficulty combinations** are the key variable, not just individual formats or difficulties. The endpoint performs well with certain combinations (MCQ+hard: 88%) but catastrophically with others (match+easy: 15%).

**Immediate wins available through:**
1. Simple routing rules to avoid bad combinations
2. Format-specific prompt additions

**Remaining structural challenge:**
- Fill-in format inherently struggles with "explain" objectives
- Consider format restrictions based on learning objective verbs
