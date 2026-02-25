"""
MCQ-Specific Evaluation Additions

Additional evaluation criteria for Multiple Choice Questions.
"""

MCQ_ADDITIONS = '''
## MCQ-SPECIFIC EVALUATION CRITERIA

### Structure Requirements
- Exactly 4 options (A, B, C, D)
- Exactly 1 correct answer
- All options should be roughly similar in length

### Distractor Quality (MCQ-specific)
For MCQ distractors, also check:
- Each distractor represents a different type of misconception
- Distractors are plausible given the stem
- No "all of the above" or "none of the above" options
- Answer options should not give away the answer through grammar clues

### Answer Position
- Verify the marked answer (A, B, C, or D) matches the stated correct answer
- The correct answer should not always be in the same position
'''
