"""
MSQ-Specific Evaluation Additions

Additional evaluation criteria for Multiple Select Questions.
"""

MSQ_ADDITIONS = '''
## MSQ-SPECIFIC EVALUATION CRITERIA

### Structure Requirements (CRITICAL)
- Exactly 5 options (A, B, C, D, E)
- Exactly 2-3 correct answers (not 1, not 4+)
- Question stem should indicate multiple answers expected

### AUTOMATIC FAILURES
The following are automatic failures for MSQ:
1. Fewer than 5 options
2. Not exactly 2-3 correct answers
3. Question doesn't indicate "select all" or "which of the following" (plural)

### Correct Answer Validation
- Each correct answer must be independently correct
- Correct answers should not be overlapping or redundant
- All correct answers should be clearly better than distractors

### Wrong Answer Quality
- Wrong answers should be plausible but clearly incorrect
- Should not be "trick" answers that could confuse careful students
'''
