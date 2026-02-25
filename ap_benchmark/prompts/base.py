"""
Master Evaluation Prompt - Dynamic, Curriculum-Aware

This is the versioned master prompt for evaluating AP Social Studies questions.
Following InceptBench methodology:

1. Curriculum context is built dynamically from the request
2. Confidence levels (GUARANTEED/HARD/SOFT) determine strictness
3. Issue-first evaluation - identify all problems before scoring
4. Binary scoring - 0.0 or 1.0 only, no partial credit

PROMPT_VERSION format: YYYY.MM.DD.revision
"""

PROMPT_VERSION = "2026.02.24.1"  # Relaxed cognitive demand - recall is OK

# The master prompt template - curriculum context is inserted dynamically
MASTER_EVALUATION_PROMPT = '''You are an expert AP Social Studies curriculum evaluator. Your mission is to REJECT bad questions and ENSURE curriculum alignment.

## YOUR ROLE

You are a quality gate. Your job is to:
1. Verify content matches what was requested (curriculum alignment)
2. Catch ALL factual errors
3. Ensure AP-level cognitive demand
4. Reject questions with structural or quality issues

**When in doubt, FAIL the question. Missing problems is worse than over-flagging.**

{curriculum_context}

## EVALUATION METHODOLOGY

### PHASE 1: CURRICULUM ALIGNMENT CHECK (CRITICAL)

Before anything else, answer these questions:
1. Does this content test the EXACT topic/skill specified in the curriculum context?
2. Is the difficulty level appropriate for what was requested?
3. Is the format correct (MCQ vs MSQ vs fill-in vs article)?

If ANY of these fail, the content fails `curriculum_alignment` which is CRITICAL.

### PHASE 2: ISSUE IDENTIFICATION

Identify ALL issues with the content. For each issue:
- Assign an ID (ISSUE1, ISSUE2, etc.)
- Identify the affected dimension
- Quote the exact problematic text
- Explain why it's problematic
- Rate severity (major/minor)

Be THOROUGH. Find every problem.

### PHASE 3: DIMENSION SCORING

Score each dimension as EXACTLY 0.0 or 1.0:
- 0.0 = FAIL (any issue affects this dimension)
- 1.0 = PASS (no issues affect this dimension)

**NO PARTIAL CREDIT.** Even one issue means 0.0 for that dimension.

### SELF-CONSISTENCY (MANDATORY)

1. Every 0.0 dimension MUST have at least one issue linked to it
2. Every issue MUST result in at least one 0.0 dimension
3. Inconsistency between issues and scores is an evaluation ERROR

## EVALUATION DIMENSIONS

### CRITICAL DIMENSIONS

**curriculum_alignment** (MOST IMPORTANT):
- Does content test the EXACT standard/skill from the curriculum context?
- Is it appropriate for the specified course and unit?
- Does difficulty match the request?
- FAIL for ANY deviation from the curriculum context

**factual_accuracy**:
- Are ALL historical/factual claims correct?
- Is the marked answer actually correct?
- Are dates, names, events, cause-effect relationships accurate?
- FAIL for ANY factual error (even minor ones)

### NON-CRITICAL DIMENSIONS

**cognitive_demand**:
- Does this require understanding of historical concepts?
- Recall and memorization questions ARE ACCEPTABLE
- PASS for questions testing factual knowledge, dates, names, events
- PASS for cause-effect relationships, even if straightforward
- Only FAIL for questions that are trivially obvious or nonsensical

**distractor_quality** (MCQ/MSQ only):
- Are distractors plausible but clearly wrong?
- Do they represent real student misconceptions?
- FAIL for absolute language ("total", "all", "never", "always")
- FAIL for obviously absurd distractors

**explanation_quality**:
- Does the explanation teach WHY the answer is correct?
- Does it address why other options are wrong?
- FAIL for missing/minimal explanations (< 2 sentences)
- FAIL if explanation just restates the answer

**clarity**:
- Is the question clear and unambiguous?
- Is grammar and spelling correct?
- FAIL for ambiguous wording or grammatical errors

**difficulty_alignment**:
- Does actual difficulty match requested difficulty?
- FAIL for easy questions marked hard or vice versa

{type_specific_additions}

{image_section}

## OUTPUT FORMAT

Respond with valid JSON only:

```json
{{
  "curriculum_match_analysis": {{
    "target_standard": "what was requested",
    "actual_content_tests": "what the content actually tests",
    "alignment_verdict": "MATCH or MISMATCH",
    "reasoning": "why it matches or doesn't"
  }},
  "issues": [
    {{
      "id": "ISSUE1",
      "dimension": "dimension_name",
      "snippet": "exact problematic text",
      "explanation": "why this is a problem",
      "severity": "major"
    }}
  ],
  "dimensions": {{
    "curriculum_alignment": {{
      "score": 1.0,
      "reasoning": "explanation of score",
      "issues": []
    }},
    "factual_accuracy": {{
      "score": 1.0,
      "reasoning": "explanation",
      "issues": []
    }},
    "cognitive_demand": {{
      "score": 1.0,
      "reasoning": "explanation",
      "issues": []
    }},
    "distractor_quality": {{
      "score": 1.0,
      "reasoning": "explanation",
      "issues": []
    }},
    "explanation_quality": {{
      "score": 1.0,
      "reasoning": "explanation",
      "issues": []
    }},
    "clarity": {{
      "score": 1.0,
      "reasoning": "explanation",
      "issues": []
    }},
    "difficulty_alignment": {{
      "score": 1.0,
      "reasoning": "explanation",
      "issues": []
    }}
  }}
}}
```

## CONTENT TO EVALUATE

{question_content}
'''


def get_evaluation_prompt(
    curriculum_context: str,
    question_content: str,
    type_specific_additions: str = "",
    has_images: bool = False,
) -> str:
    """
    Build the complete evaluation prompt.

    Args:
        curriculum_context: Dynamic curriculum context (from build_curriculum_context)
        question_content: The content to evaluate
        type_specific_additions: Type-specific evaluation criteria
        has_images: Whether images are included

    Returns:
        Complete evaluation prompt
    """
    image_section = ""
    if has_images:
        image_section = """
## IMAGE EVALUATION

This content includes image(s). Additionally evaluate:
- Does the image match the question content?
- Is the image historically accurate?
- Is the image clear and educationally appropriate?
- Does the image add value to the question?

Add image-related issues if problems are found.
"""

    return MASTER_EVALUATION_PROMPT.format(
        curriculum_context=curriculum_context,
        question_content=question_content,
        type_specific_additions=type_specific_additions,
        image_section=image_section,
    )


# Content formatters for different question types

def format_mcq_content(question_dict: dict) -> str:
    """Format MCQ for evaluation."""
    lines = [f"**Question:** {question_dict.get('question', '')}"]
    lines.append("")
    lines.append("**Options:**")

    options = question_dict.get('answer_options', [])
    for opt in options:
        if isinstance(opt, dict):
            key = opt.get('key', '?')
            text = opt.get('text', '')
            lines.append(f"  {key}) {text}")

    lines.append("")
    lines.append(f"**Correct Answer:** {question_dict.get('answer', '')}")
    lines.append("")

    explanation = question_dict.get('explanation') or question_dict.get('answer_explanation', '')
    lines.append(f"**Explanation:** {explanation}")

    return "\n".join(lines)


def format_msq_content(question_dict: dict) -> str:
    """Format MSQ for evaluation."""
    lines = [f"**Question:** {question_dict.get('question', '')}"]
    lines.append("*(Select all that apply)*")
    lines.append("")
    lines.append("**Options:**")

    options = question_dict.get('answer_options', [])
    for opt in options:
        if isinstance(opt, dict):
            key = opt.get('key', '?')
            text = opt.get('text', '')
            lines.append(f"  {key}) {text}")

    answer = question_dict.get('answer', '')
    if isinstance(answer, list):
        answer = ', '.join(answer)
    lines.append("")
    lines.append(f"**Correct Answers:** {answer}")
    lines.append("")

    explanation = question_dict.get('explanation') or question_dict.get('answer_explanation', '')
    lines.append(f"**Explanation:** {explanation}")

    return "\n".join(lines)


def format_fill_in_content(question_dict: dict) -> str:
    """Format fill-in for evaluation."""
    lines = [f"**Question:** {question_dict.get('question', '')}"]
    lines.append("")

    answer = question_dict.get('answer', '')
    if isinstance(answer, list):
        lines.append("**Answers:**")
        for ans in answer:
            if isinstance(ans, dict):
                lines.append(f"  - {ans.get('id', '?')}: {ans.get('accepted_answers', [])}")
            else:
                lines.append(f"  - {ans}")
    else:
        lines.append(f"**Answer:** {answer}")

    lines.append("")
    explanation = question_dict.get('explanation') or question_dict.get('answer_explanation', '')
    lines.append(f"**Explanation:** {explanation}")

    return "\n".join(lines)


def format_match_content(question_dict: dict) -> str:
    """Format matching question for evaluation."""
    lines = [f"**Instructions:** {question_dict.get('question', '')}"]
    lines.append("")

    # Column A
    col_a = question_dict.get('column_a', question_dict.get('terms', []))
    if col_a:
        lines.append("**Column A (Terms):**")
        for item in col_a:
            if isinstance(item, dict):
                # Support both 'text' (generator) and 'content' (legacy) field names
                text = item.get('text') or item.get('content', '')
                lines.append(f"  {item.get('id', '?')}. {text}")
            else:
                lines.append(f"  - {item}")
        lines.append("")

    # Column B
    col_b = question_dict.get('column_b', question_dict.get('definitions', []))
    if col_b:
        lines.append("**Column B (Definitions):**")
        for item in col_b:
            if isinstance(item, dict):
                # Support both 'text' (generator) and 'content' (legacy) field names
                text = item.get('text') or item.get('content', '')
                lines.append(f"  {item.get('id', '?')}. {text}")
            else:
                lines.append(f"  - {item}")
        lines.append("")

    lines.append(f"**Correct Matches:** {question_dict.get('answer', {})}")
    lines.append("")
    explanation = question_dict.get('explanation') or question_dict.get('answer_explanation', '')
    lines.append(f"**Explanation:** {explanation}")

    return "\n".join(lines)


def format_article_content(question_dict: dict) -> str:
    """Format article for evaluation."""
    lines = []

    title = question_dict.get('title', '')
    if title:
        lines.append(f"**Title:** {title}")
        lines.append("")

    lines.append("**Content:**")
    content = question_dict.get('content', question_dict.get('article', ''))
    if len(content) > 8000:
        content = content[:8000] + "\n\n... [truncated for evaluation]"
    lines.append(content)

    return "\n".join(lines)


def format_question_content(question_dict: dict, question_type: str) -> str:
    """Format question content based on type."""
    formatters = {
        'mcq': format_mcq_content,
        'msq': format_msq_content,
        'fill-in': format_fill_in_content,
        'fill_in': format_fill_in_content,
        'match': format_match_content,
        'article': format_article_content,
    }

    formatter = formatters.get(question_type, format_mcq_content)
    return formatter(question_dict)
