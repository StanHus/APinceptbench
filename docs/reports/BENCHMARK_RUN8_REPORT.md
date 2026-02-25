# Benchmark Run 8 Analysis Report

**Run ID:** `64b62b99-00b2-45b9-af76-4435e31c03b9`
**Date:** 2026-02-24
**Endpoint:** `http://192.168.1.24:8000/generate`
**Course:** APUSH

---

## Summary

| Metric | Run 7 | Run 8 | Change |
|--------|-------|-------|--------|
| Pass Rate | 62.9% | **49.4%** | **-13.5%** |
| Total Evaluated | 116 | 81 | -35 |
| Generation Errors | ~0 | 39 | +39 |

**Run 8 shows significant regression** with pass rate dropping from 62.9% to 49.4%.

---

## Critical Issue: Fill-in Collapse

| Format | Run 7 | Run 8 | Change |
|--------|-------|-------|--------|
| fill-in | 45% | **4.5%** | **-40.5%** |
| mcq | 74% | 69.4% | -4.6% |
| msq | 79% | 60.9% | -18.1% |
| match | 48% | N/A | (no data) |

**Fill-in is now catastrophically failing** - only 1 out of 22 questions passed.

---

## Format × Difficulty Matrix

| Format | Easy | Medium | Hard | Total |
|--------|------|--------|------|-------|
| **mcq** | 64% (9/14) | 70% (7/10) | **75%** (9/12) | **69.4%** |
| **msq** | 50% (3/6) | 50% (4/8) | **78%** (7/9) | **60.9%** |
| **fill-in** | 8% (1/13) | 0% (0/5) | 0% (0/4) | **4.5%** |

---

## Difficulty Analysis

| Difficulty | Run 7 | Run 8 | Change |
|------------|-------|-------|--------|
| easy | 63% | **39.4%** | **-23.6%** |
| medium | 69% | 47.8% | -21.2% |
| hard | 57% | **64.0%** | +7.0% |

**Inversion:** Hard questions now outperform easy questions.

---

## Dimension Pass Rates

| Dimension | Run 7 | Run 8 | Change |
|-----------|-------|-------|--------|
| curriculum_alignment | 85% | 87.7% | +2.7% |
| factual_accuracy | 83% | 76.5% | -6.5% |
| cognitive_demand | 68% | **63.0%** | **-5.0%** |
| difficulty_alignment | 87% | 79.0% | -8.0% |
| clarity | 95% | 72.8% | -22.2% |
| explanation_quality | 91% | 74.1% | -16.9% |
| distractor_quality | 96% | 92.6% | -3.4% |

**Multiple regressions** across clarity (-22%), explanation quality (-17%), and cognitive demand (-5%).

---

## Failure Analysis

### Fill-in Failures (21/22 = 95% failure rate)

All difficulty levels failing:
- Easy: 12/13 failed (92%)
- Medium: 5/5 failed (100%)
- Hard: 4/4 failed (100%)

### Easy Difficulty Failures (20/33 = 61% failure rate)

Easy questions are now the worst performing:
- Fill-in easy: 92% failure
- MSQ easy: 50% failure
- MCQ easy: 36% failure

---

## Generation Issues

39 out of 120 tasks failed to generate (32.5% error rate).

This reduced the sample size from 120 to 81, affecting statistical reliability.

---

## Comparison Across Runs

| Run | Pass% | Fill-in | MCQ | MSQ | CD |
|-----|-------|---------|-----|-----|-----|
| Run 2 | 65% | 66% | 61% | 82% | 67% |
| Run 7 | 63% | 45% | 74% | 79% | 68% |
| **Run 8** | **49%** | **5%** | 69% | 61% | 63% |

---

## Root Cause Analysis

### Why Run 8 Regressed

1. **Fill-in complete failure** (4.5% vs 45% in Run 7)
   - Accounts for ~21 failures
   - Would be 58% pass rate without fill-in

2. **Easy difficulty collapse** (39% vs 63% in Run 7)
   - Fill-in dominates easy failures
   - Questions may be too simple, failing cognitive demand

3. **Clarity regression** (73% vs 95% in Run 7)
   - 22-point drop in clarity scores
   - Questions becoming ambiguous

4. **Generation errors** (39 failures)
   - 32.5% of requests failed
   - Endpoint instability

---

## If Fill-in Were Removed

| Metric | With Fill-in | Without Fill-in |
|--------|--------------|-----------------|
| Total | 81 | 59 |
| Passed | 40 | 39 |
| Pass Rate | 49.4% | **66.1%** |

Removing fill-in would return pass rate to Run 2/7 levels.

---

## Key Findings

1. **Fill-in is broken** - 4.5% pass rate is catastrophic
2. **Easy difficulty failing** - 39% pass rate (worst)
3. **Hard difficulty succeeding** - 64% pass rate (best)
4. **MCQ remains reliable** - 69% pass rate
5. **Generation instability** - 32.5% error rate

---

## Trend Summary

```
Run 2:  ████████████████████████████████████████████████████ 65%
Run 7:  ██████████████████████████████████████████████████   63%
Run 8:  ████████████████████████████████████████             49%  <- REGRESSION
```

Pass rate has dropped 16 points from Run 2's peak.
