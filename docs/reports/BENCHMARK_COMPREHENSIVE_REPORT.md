# AP Question Pipeline - Comprehensive Benchmark Report

**Date:** 2026-02-24
**Endpoint:** `http://192.168.1.10:8000/generate`
**Course:** APUSH
**Runs Analyzed:** 7

---

## Executive Summary

| Run | Date | Pass Rate | Status |
|-----|------|-----------|--------|
| Run 1 | 2026-02-23 | 0.0% | Baseline (broken) |
| Run 2 | 2026-02-23 | **65.0%** | Peak performance |
| Run 3 | 2026-02-23 | 61.0% | Stable |
| Run 4 | 2026-02-23 | 49.6% | Regression |
| Run 5 | 2026-02-23 | 53.4% | Decline continues |
| Run 6 | 2026-02-23 | 50.0% | Low point |
| Run 7 | 2026-02-24 | 62.9% | Recovery |

**Current State:** 62.9% pass rate, near Run 2 levels but not exceeding them.

---

## Part 1: Overall Trends

### Pass Rate Over Time

```
Run 1  |                                                    | 0.0%
Run 2  |████████████████████████████████████████████████████| 65.0%  <- PEAK
Run 3  |████████████████████████████████████████████████    | 61.0%
Run 4  |███████████████████████████████████████             | 49.6%
Run 5  |██████████████████████████████████████████          | 53.4%
Run 6  |████████████████████████████████████████            | 50.0%
Run 7  |██████████████████████████████████████████████████  | 62.9%  <- CURRENT
       0%                    50%                         100%
```

### Key Metrics Across All Runs

| Run | Total | Passed | Failed | Pass Rate | Avg Score |
|-----|-------|--------|--------|-----------|-----------|
| Run 1 | 117 | 0 | 117 | 0.0% | N/A |
| Run 2 | 117 | 76 | 41 | 65.0% | 0.826 |
| Run 3 | 118 | 72 | 46 | 61.0% | ~0.81 |
| Run 4 | 113 | 56 | 57 | 49.6% | ~0.77 |
| Run 5 | 118 | 63 | 55 | 53.4% | ~0.80 |
| Run 6 | 116 | 58 | 58 | 50.0% | 0.801 |
| Run 7 | 116 | 73 | 43 | 62.9% | ~0.82 |

---

## Part 2: Dimension Analysis

### Dimension Pass Rates by Run

| Dimension | R1 | R2 | R3 | R4 | R5 | R6 | R7 |
|-----------|----|----|----|----|----|----|-----|
| curriculum_alignment | 0% | **89%** | 90% | 77% | 83% | 87% | 85% |
| factual_accuracy | 0% | 79% | 81% | 75% | 84% | **85%** | 83% |
| cognitive_demand | 0% | 67% | **69%** | **70%** | 59% | 51% | 68% |
| difficulty_alignment | 0% | 86% | 83% | **90%** | 81% | 84% | 87% |
| clarity | 0% | **97%** | 95% | 85% | 85% | 82% | 95% |
| explanation_quality | 0% | 92% | 91% | 87% | **95%** | 90% | 91% |
| distractor_quality | 0% | **97%** | 96% | 90% | 94% | 96% | 96% |

### The Critical Discovery: Cognitive Demand Drives Pass Rate

```
Run    Pass%   CD%    Correlation
─────────────────────────────────
Run 2   65%    67%    ████████████████████████████████████
Run 3   61%    69%    ██████████████████████████████████
Run 4   50%    70%    ████████████████████████████  (CA dropped to 77%)
Run 5   53%    59%    ██████████████████████████████
Run 6   50%    51%    ████████████████████████████
Run 7   63%    68%    ███████████████████████████████████
```

**Finding:** Pass rate correlates strongly with cognitive demand, except when curriculum alignment drops below ~80%.

### Dimension Failure Impact

| Dimension | Avg Failures/Run | Impact on Pass Rate |
|-----------|------------------|---------------------|
| cognitive_demand | 38 | **PRIMARY DRIVER** |
| curriculum_alignment | 16 | Secondary driver |
| factual_accuracy | 20 | Moderate impact |
| difficulty_alignment | 16 | Moderate impact |
| explanation_quality | 10 | Low impact |
| clarity | 10 | Low impact |
| distractor_quality | 5 | Minimal impact |

---

## Part 3: Format Analysis

### Format Pass Rates by Run

| Format | R2 | R3 | R4 | R5 | R6 | R7 | Avg |
|--------|----|----|----|----|----|----|-----|
| **msq** | **82%** | 71% | 62% | 77% | 65% | **79%** | **73%** |
| **mcq** | 61% | **76%** | 61% | 70% | 71% | **74%** | **69%** |
| match | 53% | 45% | 52% | 55% | 54% | 48% | **51%** |
| fill-in | 66% | 50% | **21%** | 25% | 23% | 45% | **38%** |

### Format Performance Visualization

```
MSQ      |████████████████████████████████████████████████████████████████████████| 73%
MCQ      |████████████████████████████████████████████████████████████████████    | 69%
Match    |████████████████████████████████████████████                            | 51%
Fill-in  |██████████████████████████████████                                      | 38%
         0%                              50%                                    100%
```

### Format × Difficulty Matrix (Run 7)

|          | Easy | Medium | Hard | Total |
|----------|------|--------|------|-------|
| **msq**  | 77% (10/13) | 83% (10/12) | 75% (3/4) | **79%** |
| **mcq**  | 57% (8/14) | **91%** (10/11) | 78% (7/9) | **74%** |
| match    | 50% (3/6) | 44% (4/9) | 50% (9/18) | **48%** |
| fill-in  | 57% (4/7) | 43% (3/7) | 33% (2/6) | **45%** |

### Format Recommendations

| Format | Status | Evidence |
|--------|--------|----------|
| **MSQ** | Best performer | 73% avg, consistent across runs |
| **MCQ** | Strong performer | 69% avg, 91% at medium difficulty |
| **Match** | Problematic | 51% avg, no improvement over 7 runs |
| **Fill-in** | Critical failure | 38% avg, dropped to 21% in Run 4 |

---

## Part 4: Difficulty Analysis

### Difficulty Pass Rates by Run

| Difficulty | R2 | R3 | R4 | R5 | R6 | R7 | Avg |
|------------|----|----|----|----|----|----|-----|
| easy | 66% | 46% | 27% | **68%** | 55% | 63% | **54%** |
| medium | **79%** | 68% | 63% | 54% | 46% | **69%** | **63%** |
| hard | 50% | **69%** | 58% | 38% | 49% | 57% | **54%** |

### Difficulty Analysis

```
Easy    |████████████████████████████████████████████████████████            | 54%
Medium  |████████████████████████████████████████████████████████████████    | 63%  <- BEST
Hard    |████████████████████████████████████████████████████████            | 54%
        0%                              50%                               100%
```

**Finding:** Medium difficulty consistently outperforms easy and hard.

### Difficulty × Format Best Performers

| Rank | Combination | Pass Rate | Sample Size |
|------|-------------|-----------|-------------|
| 1 | MCQ + Medium | 91% | 11 |
| 2 | MSQ + Medium | 83% | 12 |
| 3 | MSQ + Easy | 77% | 13 |
| 4 | MCQ + Hard | 78% | 9 |
| 5 | MSQ + Hard | 75% | 4 |

### Difficulty × Format Worst Performers

| Rank | Combination | Pass Rate | Sample Size |
|------|-------------|-----------|-------------|
| 1 | Fill-in + Hard | 33% | 6 |
| 2 | Fill-in + Medium | 43% | 7 |
| 3 | Match + Medium | 44% | 9 |
| 4 | Match + Easy | 50% | 6 |
| 5 | Match + Hard | 50% | 18 |

---

## Part 5: Failure Analysis

### Top Failure Reasons (Run 7)

| Dimension | Count | % of Failures | Primary Cause |
|-----------|-------|---------------|---------------|
| factual_accuracy | 20 | 47% | Wrong dates, incorrect legislation |
| cognitive_demand | 20 | 47% | Recall-only questions |
| curriculum_alignment | 17 | 40% | Wrong time periods |
| difficulty_alignment | 11 | 26% | Match format too easy |
| explanation_quality | 10 | 23% | Superficial explanations |
| clarity | 5 | 12% | Ambiguous wording |
| distractor_quality | 4 | 9% | No distractors in matching |

### Failure Patterns by Format

#### Fill-in Failures (55% failure rate)

Primary issues:
- Tests vocabulary recall, not analysis
- Cannot assess "explain how/why" objectives
- Blanks make answers obvious with context

```
Example failure:
  Learning Objective: "Explain causes of the Columbian Exchange"
  Generated: Fill-in-blank for term "Atlantic World"
  Problem: Tests vocabulary, not causation
```

#### Match Failures (52% failure rate)

Primary issues:
- 1:1 matching without distractors
- Redundant terms reduce challenge
- Cannot achieve hard difficulty

```
Example failure:
  Requested: Hard difficulty matching
  Generated: 4 terms matched to 4 definitions (no extras)
  Problem: Simple elimination, not analysis
```

### Cognitive Demand Failure Examples

```
"Question requires only basic recall of information directly
provided in curriculum materials without requiring analysis"

"While the question requires understanding consequences, the
redundant terms reduce the analytical challenge significantly"

"This is primarily a recall question asking students to identify
factual statements rather than requiring analytical thinking"
```

### Factual Accuracy Failure Examples

```
"Contains a factual error regarding the name of the legislation
that created Medicare and Medicaid"

"Factual error regarding time period - the curriculum specifies
1877-1900, but explanation references 1865-1877"

"Settlement houses framed as Gilded Age (1865-1898) when they
were Progressive Era (1890s-1920s)"
```

### Curriculum Alignment Failure Examples

```
"Content tests the correct topic but focuses on the wrong time
period. The curriculum specifies 1877-1900 but content examines
Reconstruction policies from 1865-1877"

"Question expands beyond specified curriculum - request mentioned
Iraq and Afghanistan, but response includes Syria and Libya"
```

---

## Part 6: Run-by-Run Analysis

### Run 1: Baseline (0% pass rate)

- **Status:** Complete failure
- **Cause:** Endpoint not using curriculum context
- **All dimensions:** 0% pass rate

### Run 2: Peak Performance (65% pass rate)

- **Key improvement:** Curriculum alignment 0% → 89%
- **What worked:** Endpoint started using `learning_objective` and `statement` fields
- **Best format:** MSQ at 82%
- **Remaining issues:** Cognitive demand at 67%, fill-in at 66%

### Run 3: Stable (61% pass rate)

- **Status:** Minor regression (-4%)
- **Dimensions:** All stable or improved
- **Fill-in:** Dropped to 50% (first warning sign)

### Run 4: Regression (49.6% pass rate)

- **Key failure:** Curriculum alignment dropped to 77%
- **Paradox:** Cognitive demand peaked at 70% but CA failure dragged down pass rate
- **Fill-in:** Collapsed to 21%
- **Easy difficulty:** Dropped to 27%

### Run 5: Continued Decline (53.4% pass rate)

- **Key failure:** Cognitive demand dropped to 59%
- **CA recovery:** Back to 83%
- **Pattern:** Trade-off between CA and CD begins

### Run 6: Low Point (50% pass rate)

- **Key failure:** Cognitive demand collapsed to 51%
- **Other metrics:** All stable or improved
- **Diagnosis:** "Content-accurate but cognitively shallow questions"
- **Fill-in:** Remained at 23%

### Run 7: Recovery (62.9% pass rate)

- **Key improvement:** Cognitive demand recovered to 68%
- **Status:** Near Run 2 levels
- **Best performers:** MCQ (74%), MSQ (79%)
- **Remaining issues:** Fill-in (45%), Match (48%)

---

## Part 7: Root Cause Analysis

### Why Run 2 Succeeded

1. **Curriculum alignment fixed (89%)** - Endpoint properly used learning objectives
2. **Format balance** - All formats performed reasonably (53-82%)
3. **Cognitive demand adequate (67%)** - Not great, but sufficient

### Why Runs 4-6 Regressed

| Run | Primary Failure | Secondary Failure |
|-----|-----------------|-------------------|
| Run 4 | CA dropped to 77% | Fill-in collapsed to 21% |
| Run 5 | CD dropped to 59% | Hard difficulty at 38% |
| Run 6 | CD collapsed to 51% | Fill-in remained at 23% |

### The Pass Rate Formula

```
Pass Rate ≈ f(Cognitive Demand, Curriculum Alignment)

Requirements for >60% pass rate:
  - Curriculum Alignment ≥ 85%
  - Cognitive Demand ≥ 65%
  - Both conditions must be met simultaneously
```

Evidence:
- Run 4: CD=70% but CA=77% → 49.6% (CA failed)
- Run 6: CA=87% but CD=51% → 50.0% (CD failed)
- Run 2: CA=89% and CD=67% → 65.0% (both passed)
- Run 7: CA=85% and CD=68% → 62.9% (both passed)

---

## Part 8: Format-Specific Findings

### MSQ: Best Format (73% avg)

| Metric | Value |
|--------|-------|
| Average pass rate | 73% |
| Best run | Run 2 (82%) |
| Worst run | Run 4 (62%) |
| Best difficulty | Medium (83%) |

**Why MSQ works:**
- Forces evaluation of multiple factors
- Cannot be answered through pattern matching
- Naturally aligns with "explain" learning objectives

### MCQ: Strong Format (69% avg)

| Metric | Value |
|--------|-------|
| Average pass rate | 69% |
| Best run | Run 3 (76%) |
| Worst run | Run 2, 4 (61%) |
| Best difficulty | Medium (91%) |

**Why MCQ works:**
- Distractors based on common misconceptions
- Can test causal reasoning
- Good for factual accuracy

### Match: Problematic Format (51% avg)

| Metric | Value |
|--------|-------|
| Average pass rate | 51% |
| Best run | Run 5 (55%) |
| Worst run | Run 3 (45%) |
| Never exceeds | 55% |

**Why Match fails:**
- 1:1 format eliminates analytical challenge
- No distractors = simple elimination
- Cannot achieve "hard" difficulty authentically

### Fill-in: Critical Failure (38% avg)

| Metric | Value |
|--------|-------|
| Average pass rate | 38% |
| Best run | Run 2 (66%) |
| Worst run | Run 4 (21%) |
| Collapsed after | Run 2 |

**Why Fill-in fails:**
- Inherently tests vocabulary recall
- Cannot assess "explain how/why"
- Context makes blanks obvious

---

## Part 9: Data Archive

### Available Files

| File | Size | Contents |
|------|------|----------|
| `latest_run_failures.json` | 100KB | All 43 Run 7 failures with full details |
| `BENCHMARK_RUN2_REPORT.md` | 10KB | Peak performance analysis |
| `BENCHMARK_RUN6_REPORT.md` | 8KB | Low point analysis |
| `BENCHMARK_RUN7_REPORT.md` | 3KB | Recovery analysis |

### Database Collections

| Collection | Documents | Contents |
|------------|-----------|----------|
| `pipeline_results` | 939 | All evaluation results |
| `pipeline_requests` | 971 | All generation requests |
| `pipeline_runs` | 9 | Run metadata |

### Run IDs

| Run | Run ID |
|-----|--------|
| Run 1 | `217a76cf-18f2-4b2b-8257-e69d12f78296` |
| Run 2 | `9f5f50a1-b7bc-446b-9011-8ae59e59861a` |
| Run 3 | `3d7ab8e7-170e-4a2e-83e3-b859fe8ef102` |
| Run 4 | `b835d6db-13be-4805-9fa7-8f5392b2ad96` |
| Run 5 | `73ced3ed-1cc6-4f34-8d82-7a948976c847` |
| Run 6 | `99e462b0-1ae5-4fac-ac4e-b4923276bd67` |
| Run 7 | `7084f6e5-4431-4998-a49c-1236af5989c9` |

---

## Part 10: Conclusions

### Current State

- **Pass rate:** 62.9% (Run 7)
- **Status:** Recovered to near-peak levels
- **Trend:** Stable after recovery from 50% low

### What Works

| Factor | Evidence |
|--------|----------|
| MSQ format | 73% average, consistent performer |
| MCQ format | 69% average, 91% at medium difficulty |
| Medium difficulty | 63% average, best of all difficulties |
| High curriculum alignment | Required for >60% pass rate |
| Adequate cognitive demand | Required for >60% pass rate |

### What Fails

| Factor | Evidence |
|--------|----------|
| Fill-in format | 38% average, collapsed to 21% |
| Match format | 51% average, never exceeds 55% |
| Hard difficulty | 54% average, inconsistent |
| Low cognitive demand | Directly causes pass rate drops |

### Critical Dependencies

```
Pass Rate = f(CA, CD)

Where:
  CA (Curriculum Alignment) ≥ 85% required
  CD (Cognitive Demand) ≥ 65% required

If either fails, pass rate drops below 55%
```

### Unresolved Issues

1. **Cognitive demand volatility** - Ranges from 51% to 70% across runs
2. **Fill-in format** - Never recovered after Run 2
3. **Match format** - Structurally unable to achieve analytical depth
4. **Hard difficulty** - Inconsistent, often fails difficulty alignment

---

## Appendix: Raw Data Summary

### Questions Evaluated per Run

| Run | fill-in | match | mcq | msq | Total |
|-----|---------|-------|-----|-----|-------|
| Run 1 | 34 | 37 | 31 | 15 | 117 |
| Run 2 | 32 | 34 | 23 | 28 | 117 |
| Run 3 | 22 | 33 | 29 | 34 | 118 |
| Run 4 | 28 | 25 | 31 | 29 | 113 |
| Run 5 | 36 | 33 | 23 | 26 | 118 |
| Run 6 | 39 | 26 | 28 | 23 | 116 |
| Run 7 | 20 | 33 | 34 | 29 | 116 |

### Pass Counts per Format per Run

| Run | fill-in | match | mcq | msq | Total |
|-----|---------|-------|-----|-----|-------|
| Run 1 | 0 | 0 | 0 | 0 | 0 |
| Run 2 | 21 | 18 | 14 | 23 | 76 |
| Run 3 | 11 | 15 | 22 | 24 | 72 |
| Run 4 | 6 | 13 | 19 | 18 | 56 |
| Run 5 | 9 | 18 | 16 | 20 | 63 |
| Run 6 | 9 | 14 | 20 | 15 | 58 |
| Run 7 | 9 | 16 | 25 | 23 | 73 |

---

*Report generated: 2026-02-24*
*Data source: MongoDB `ap_social_studies` database*
