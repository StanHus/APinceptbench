"""
Official AP Question Type Evaluation Prompts

Based on College Board's official question types and rubrics:
- MCQ: Multiple Choice (all courses)
- SAQ: Short Answer Question (History courses)
- DBQ: Document-Based Question (History courses)
- LEQ: Long Essay Question (History courses)
- FRQ: Free Response Questions (Gov/HumanGeo specific types)

Each prompt evaluates against the official AP rubric dimensions.

PROMPT_VERSION format: YYYY.MM.DD.revision
"""

PROMPT_VERSION = "2026.02.24.2"  # Added MCQ_SET prompt, fixed formatters

# =============================================================================
# MCQ - Multiple Choice Question Evaluation
# =============================================================================

MCQ_EVALUATION_PROMPT = '''You are an expert AP Social Studies curriculum evaluator. Evaluate this Multiple Choice Question (MCQ) against official AP standards.

## CURRICULUM CONTEXT
{curriculum_context}

## MCQ REQUIREMENTS

AP MCQs must:
1. Have exactly ONE correct answer that is historically defensible
2. Include plausible distractors representing common misconceptions
3. Test appropriate AP skills (sourcing, causation, comparison, contextualization)
4. Be answerable from the stimulus (if provided) combined with course knowledge
5. Avoid absolute language ("always", "never", "all", "none") unless historically accurate

## EVALUATION DIMENSIONS

### CRITICAL DIMENSIONS (any failure = question fails)

**factual_accuracy** (0.0 or 1.0):
- Is the correct answer historically accurate?
- Are all answer options factually defensible as written?
- Are dates, names, events correct?

**answer_validity** (0.0 or 1.0):
- Is there exactly ONE correct answer?
- Is the correct answer clearly the BEST answer?
- Could a knowledgeable student defend any other answer as correct?

**stimulus_alignment** (0.0 or 1.0) - if stimulus provided:
- Does the question require analysis of the stimulus?
- Can the question be answered from the stimulus + course knowledge?
- Is the stimulus historically authentic or properly attributed?

### NON-CRITICAL DIMENSIONS

**distractor_quality** (0.0 or 1.0):
- Are distractors plausible but clearly incorrect?
- Do they represent real student misconceptions?
- Are they parallel in structure to the correct answer?
- FAIL for obviously absurd options or absolute language traps

**skill_alignment** (0.0 or 1.0):
- Does this test an appropriate AP skill?
- Skills: sourcing, causation, comparison, contextualization, argumentation
- FAIL for pure trivia that doesn't require historical thinking

**clarity** (0.0 or 1.0):
- Is the question stem clear and unambiguous?
- Are answer options clearly written?
- Is grammar and spelling correct?

## CONTENT TO EVALUATE

{question_content}

## OUTPUT FORMAT

Respond with valid JSON only:

```json
{{
  "question_type": "mcq",
  "issues": [
    {{
      "id": "ISSUE1",
      "dimension": "dimension_name",
      "snippet": "exact problematic text",
      "explanation": "why this is a problem",
      "severity": "major|minor"
    }}
  ],
  "dimensions": {{
    "factual_accuracy": {{"score": 1.0, "reasoning": "...", "issues": []}},
    "answer_validity": {{"score": 1.0, "reasoning": "...", "issues": []}},
    "stimulus_alignment": {{"score": 1.0, "reasoning": "...", "issues": []}},
    "distractor_quality": {{"score": 1.0, "reasoning": "...", "issues": []}},
    "skill_alignment": {{"score": 1.0, "reasoning": "...", "issues": []}},
    "clarity": {{"score": 1.0, "reasoning": "...", "issues": []}}
  }},
  "overall_assessment": "PASS or FAIL with brief explanation"
}}
```
'''

# =============================================================================
# MCQ_SET - Multiple Choice Question Set Evaluation
# =============================================================================

MCQ_SET_EVALUATION_PROMPT = '''You are an expert AP Social Studies curriculum evaluator. Evaluate this MCQ Stimulus Set against official AP standards.

## CURRICULUM CONTEXT
{curriculum_context}

## MCQ SET REQUIREMENTS

An MCQ Stimulus Set consists of:
1. A shared stimulus (primary source, image, data, etc.)
2. 3-4 questions that ALL reference the stimulus
3. Each question follows standard MCQ rules

## EVALUATION DIMENSIONS

### CRITICAL DIMENSIONS (any failure = question fails)

**factual_accuracy** (0.0 or 1.0):
- Is the stimulus historically accurate?
- Are all correct answers historically accurate?
- Are dates, names, events correct?

**answer_validity** (0.0 or 1.0):
- Does EACH question have exactly ONE correct answer?
- Are all correct answers clearly the BEST answers?
- FAIL if ANY question has ambiguous correct answer

**stimulus_alignment** (0.0 or 1.0):
- Is a stimulus provided?
- Do ALL questions require analysis of the stimulus?
- FAIL if questions can be answered without the stimulus

### NON-CRITICAL DIMENSIONS

**distractor_quality** (0.0 or 1.0):
- Are distractors plausible across all questions?
- Do they represent real student misconceptions?

**skill_alignment** (0.0 or 1.0):
- Do questions test different AP skills?
- Skills: sourcing, causation, comparison, contextualization

**clarity** (0.0 or 1.0):
- Are all question stems clear?
- Are answer options clearly written?

## CONTENT TO EVALUATE

{question_content}

## OUTPUT FORMAT

Respond with valid JSON only:

```json
{{
  "question_type": "mcq_set",
  "stimulus_present": true,
  "question_count": 3,
  "issues": [
    {{
      "id": "ISSUE1",
      "question_number": 1,
      "dimension": "dimension_name",
      "snippet": "exact problematic text",
      "explanation": "why this is a problem",
      "severity": "major|minor"
    }}
  ],
  "dimensions": {{
    "factual_accuracy": {{"score": 1.0, "reasoning": "...", "issues": []}},
    "answer_validity": {{"score": 1.0, "reasoning": "...", "issues": []}},
    "stimulus_alignment": {{"score": 1.0, "reasoning": "...", "issues": []}},
    "distractor_quality": {{"score": 1.0, "reasoning": "...", "issues": []}},
    "skill_alignment": {{"score": 1.0, "reasoning": "...", "issues": []}},
    "clarity": {{"score": 1.0, "reasoning": "...", "issues": []}}
  }},
  "overall_assessment": "PASS or FAIL with brief explanation"
}}
```
'''

# =============================================================================
# SAQ - Short Answer Question Evaluation
# =============================================================================

SAQ_EVALUATION_PROMPT = '''You are an expert AP History curriculum evaluator. Evaluate this Short Answer Question (SAQ) against official AP standards.

## CURRICULUM CONTEXT
{curriculum_context}

## SAQ REQUIREMENTS (Official College Board)

Structure:
- 3 parts: (a), (b), (c)
- Each part worth 1 point (total 3 points)
- Response should be 3-4 sentences per part
- May include stimulus (document, image, data)

Each part must:
1. Have a clear task verb (identify, describe, explain, compare)
2. Be answerable with specific historical evidence
3. Test historical thinking skills (causation, comparison, contextualization)
4. Have unambiguous scoring criteria

## OFFICIAL SAQ RUBRIC

| Part | Points | Requirement |
|------|--------|-------------|
| (a) | 0-1 | Accomplishes task A with specific historical evidence |
| (b) | 0-1 | Accomplishes task B with specific historical evidence |
| (c) | 0-1 | Accomplishes task C with specific historical evidence |

## EVALUATION DIMENSIONS

### CRITICAL DIMENSIONS

**prompt_structure** (0.0 or 1.0):
- Does it have exactly 3 parts: (a), (b), (c)?
- Does each part have a clear task verb?
- Are parts logically connected but independently scorable?

**historical_specificity** (0.0 or 1.0):
- Does each part require SPECIFIC historical evidence?
- FAIL if parts can be answered with generalizations
- FAIL if no clear historical content required

**answerability** (0.0 or 1.0):
- Can each part be answered with AP course content?
- Is there sufficient evidence available in the curriculum?
- FAIL if parts require obscure knowledge

### NON-CRITICAL DIMENSIONS

**skill_alignment** (0.0 or 1.0):
- Does it test causation, comparison, or contextualization?
- FAIL for pure recall without historical thinking

**stimulus_integration** (0.0 or 1.0) - if stimulus present:
- Do parts require analysis of the stimulus?
- Is the stimulus historically relevant?

**scoring_clarity** (0.0 or 1.0):
- Is it clear what earns each point?
- Are acceptable answers unambiguous?

## CONTENT TO EVALUATE

{question_content}

## OUTPUT FORMAT

Respond with valid JSON only:

```json
{{
  "question_type": "saq",
  "issues": [...],
  "dimensions": {{
    "prompt_structure": {{"score": 1.0, "reasoning": "...", "issues": []}},
    "historical_specificity": {{"score": 1.0, "reasoning": "...", "issues": []}},
    "answerability": {{"score": 1.0, "reasoning": "...", "issues": []}},
    "skill_alignment": {{"score": 1.0, "reasoning": "...", "issues": []}},
    "stimulus_integration": {{"score": 1.0, "reasoning": "...", "issues": []}},
    "scoring_clarity": {{"score": 1.0, "reasoning": "...", "issues": []}}
  }},
  "rubric_alignment": {{
    "part_a": {{"task_verb": "...", "evidence_required": "...", "scorable": true}},
    "part_b": {{"task_verb": "...", "evidence_required": "...", "scorable": true}},
    "part_c": {{"task_verb": "...", "evidence_required": "...", "scorable": true}}
  }},
  "overall_assessment": "PASS or FAIL"
}}
```
'''

# =============================================================================
# DBQ - Document-Based Question Evaluation
# =============================================================================

DBQ_EVALUATION_PROMPT = '''You are an expert AP History curriculum evaluator. Evaluate this Document-Based Question (DBQ) against the official College Board rubric.

## CURRICULUM CONTEXT
{curriculum_context}

## DBQ REQUIREMENTS (Official College Board 2024)

Structure:
- 1 argumentative prompt
- **Exactly 7 documents** with proper attribution
- Documents must represent multiple perspectives
- 60 minutes total (15-min reading + 45-min writing)

## OFFICIAL DBQ RUBRIC (7 Points)

| Category | Points | Requirement |
|----------|--------|-------------|
| **Thesis/Claim** | 0-1 | Historically defensible thesis establishing line of reasoning |
| **Contextualization** | 0-1 | Describes broader historical context relevant to prompt |
| **Evidence (Documents)** | 0-2 | Uses 3+ docs (1pt) OR 4+ docs supporting argument (2pts) |
| **Evidence (Outside)** | 0-1 | Uses specific evidence beyond the documents |
| **Sourcing (HIPP)** | 0-1 | Explains how 2+ docs' POV/purpose/situation/audience is relevant |
| **Complexity** | 0-1 | Sophisticated argument OR all 7 docs + HIPP on 4 docs |

## EVALUATION DIMENSIONS

### CRITICAL DIMENSIONS

**document_count** (0.0 or 1.0):
- Are there EXACTLY 7 documents?
- FAIL immediately if not 7 documents

**document_authenticity** (0.0 or 1.0):
- Are documents historically accurate or properly simulated?
- Does each document have proper attribution (author, date, source)?
- Are visual documents accurately described/represented?

**document_diversity** (0.0 or 1.0):
- Do documents represent MULTIPLE perspectives on the issue?
- Are there different document types (primary, secondary, visual, quantitative)?
- FAIL if all documents support the same viewpoint

**prompt_arguability** (0.0 or 1.0):
- Does the prompt require an ARGUMENTATIVE thesis?
- Are there multiple defensible positions?
- FAIL if only one valid answer exists

**document_relevance** (0.0 or 1.0):
- Are ALL 7 documents relevant to the prompt?
- Can each document support or complicate an argument?

### NON-CRITICAL DIMENSIONS

**thesis_potential** (0.0 or 1.0):
- Can students construct multiple different valid theses?
- Is there room for nuanced argument?

**sourcing_opportunity** (0.0 or 1.0):
- Do documents allow for HIPP analysis?
- (Historical situation, Intended audience, Purpose, Point of view)
- Can students explain WHY document perspective matters?

**outside_evidence_scope** (0.0 or 1.0):
- Is it clear what outside evidence would be relevant?
- Can students reasonably know relevant outside evidence?

**time_period_accuracy** (0.0 or 1.0):
- Do all documents match the specified time period?
- Is the prompt time period clear?

## CONTENT TO EVALUATE

{question_content}

## OUTPUT FORMAT

Respond with valid JSON only:

```json
{{
  "question_type": "dbq",
  "document_analysis": {{
    "total_documents": 7,
    "document_types": ["primary text", "secondary text", "image", "chart", etc.],
    "perspectives_represented": ["perspective 1", "perspective 2", ...],
    "time_period_coverage": "1800-1850",
    "attribution_complete": true
  }},
  "issues": [...],
  "dimensions": {{
    "document_count": {{"score": 1.0, "reasoning": "...", "issues": []}},
    "document_authenticity": {{"score": 1.0, "reasoning": "...", "issues": []}},
    "document_diversity": {{"score": 1.0, "reasoning": "...", "issues": []}},
    "prompt_arguability": {{"score": 1.0, "reasoning": "...", "issues": []}},
    "document_relevance": {{"score": 1.0, "reasoning": "...", "issues": []}},
    "thesis_potential": {{"score": 1.0, "reasoning": "...", "issues": []}},
    "sourcing_opportunity": {{"score": 1.0, "reasoning": "...", "issues": []}},
    "outside_evidence_scope": {{"score": 1.0, "reasoning": "...", "issues": []}},
    "time_period_accuracy": {{"score": 1.0, "reasoning": "...", "issues": []}}
  }},
  "rubric_feasibility": {{
    "thesis_point": "achievable - multiple valid positions exist",
    "context_point": "achievable - clear historical context available",
    "evidence_points": "achievable - 7 usable documents",
    "outside_evidence_point": "achievable - relevant outside evidence exists",
    "sourcing_point": "achievable - documents allow HIPP analysis",
    "complexity_point": "achievable - nuanced argument possible"
  }},
  "overall_assessment": "PASS or FAIL"
}}
```
'''

# =============================================================================
# LEQ - Long Essay Question Evaluation
# =============================================================================

LEQ_EVALUATION_PROMPT = '''You are an expert AP History curriculum evaluator. Evaluate this Long Essay Question (LEQ) against the official College Board rubric.

## CURRICULUM CONTEXT
{curriculum_context}

## LEQ REQUIREMENTS (Official College Board 2024)

Structure:
- 1 argumentative prompt (no documents provided)
- Tests specific historical reasoning skill
- Students choose from 3 prompts (different time periods)
- 40 minutes recommended

Historical Reasoning Types:
- **Causation**: Explain causes and/or effects
- **Comparison**: Compare and/or contrast
- **Continuity and Change (CCOT)**: Analyze patterns over time

## OFFICIAL LEQ RUBRIC (6 Points)

| Category | Points | Requirement |
|----------|--------|-------------|
| **Thesis/Claim** | 0-1 | Historically defensible thesis establishing line of reasoning |
| **Contextualization** | 0-1 | Describes broader historical context relevant to prompt |
| **Evidence** | 0-2 | Identifies evidence (1pt) OR uses evidence to support argument (2pts) |
| **Analysis & Reasoning** | 0-2 | Uses historical reasoning (1pt) OR demonstrates complexity (2pts) |

## EVALUATION DIMENSIONS

### CRITICAL DIMENSIONS

**prompt_arguability** (0.0 or 1.0):
- Does the prompt require an ARGUMENTATIVE thesis?
- Can students take multiple defensible positions?
- FAIL if only one valid answer exists

**reasoning_type** (0.0 or 1.0):
- Does the prompt clearly require causation, comparison, OR CCOT?
- Is the reasoning type explicit or clearly implied?
- FAIL if reasoning type is ambiguous

**time_period_specificity** (0.0 or 1.0):
- Are time boundaries clear?
- Does the prompt specify a historical period?
- FAIL for open-ended time frames

**evidence_accessibility** (0.0 or 1.0):
- Can students cite specific evidence from the AP curriculum?
- Is there sufficient relevant content in the course?
- FAIL if requires obscure knowledge

### NON-CRITICAL DIMENSIONS

**thesis_flexibility** (0.0 or 1.0):
- Can students construct multiple different valid theses?
- Is there room for original argument?

**complexity_opportunity** (0.0 or 1.0):
- Can students demonstrate nuanced understanding?
- Does the topic allow for multiple causes/effects, contradictions, or connections across periods?

**contextualization_opportunity** (0.0 or 1.0):
- Is there clear broader historical context available?
- Can students situate the topic in larger developments?

## CONTENT TO EVALUATE

{question_content}

## OUTPUT FORMAT

Respond with valid JSON only:

```json
{{
  "question_type": "leq",
  "prompt_analysis": {{
    "reasoning_type": "causation|comparison|ccot",
    "time_period": "1800-1848",
    "topic_focus": "...",
    "arguable_positions": ["position 1", "position 2", ...]
  }},
  "issues": [...],
  "dimensions": {{
    "prompt_arguability": {{"score": 1.0, "reasoning": "...", "issues": []}},
    "reasoning_type": {{"score": 1.0, "reasoning": "...", "issues": []}},
    "time_period_specificity": {{"score": 1.0, "reasoning": "...", "issues": []}},
    "evidence_accessibility": {{"score": 1.0, "reasoning": "...", "issues": []}},
    "thesis_flexibility": {{"score": 1.0, "reasoning": "...", "issues": []}},
    "complexity_opportunity": {{"score": 1.0, "reasoning": "...", "issues": []}},
    "contextualization_opportunity": {{"score": 1.0, "reasoning": "...", "issues": []}}
  }},
  "rubric_feasibility": {{
    "thesis_point": "achievable - multiple valid positions exist",
    "context_point": "achievable - clear historical context available",
    "evidence_points": "achievable - sufficient course content available",
    "reasoning_points": "achievable - clear reasoning type and complexity opportunity"
  }},
  "overall_assessment": "PASS or FAIL"
}}
```
'''

# =============================================================================
# AP GOV FRQ Types
# =============================================================================

APGOV_CONCEPT_APPLICATION_PROMPT = '''You are an expert AP Government curriculum evaluator. Evaluate this Concept Application FRQ.

## CURRICULUM CONTEXT
{curriculum_context}

## CONCEPT APPLICATION REQUIREMENTS

Structure:
- Realistic political scenario
- 3-4 parts with task verbs (describe, explain, apply)
- Tests application of specific course concepts

## EVALUATION DIMENSIONS

**scenario_realism** (0.0 or 1.0): Plausible political scenario
**concept_accuracy** (0.0 or 1.0): Course concepts correctly represented
**part_clarity** (0.0 or 1.0): Clear task verbs and scoring criteria
**application_requirement** (0.0 or 1.0): Requires application, not just recall

## CONTENT TO EVALUATE

{question_content}

## OUTPUT FORMAT

```json
{{
  "question_type": "apgov_concept_application",
  "issues": [...],
  "dimensions": {{...}},
  "overall_assessment": "PASS or FAIL"
}}
```
'''

APGOV_QUANTITATIVE_PROMPT = '''You are an expert AP Government curriculum evaluator. Evaluate this Quantitative Analysis FRQ.

## CURRICULUM CONTEXT
{curriculum_context}

## QUANTITATIVE ANALYSIS REQUIREMENTS

Structure:
- Visual data (chart, graph, table, infographic)
- 3-4 parts analyzing data and connecting to political concepts

## EVALUATION DIMENSIONS

**data_accuracy** (0.0 or 1.0): Data is accurate or realistic
**data_clarity** (0.0 or 1.0): Visualization is clear and readable
**analysis_requirement** (0.0 or 1.0): Requires trend identification and explanation
**concept_connection** (0.0 or 1.0): Links data to political principles

## CONTENT TO EVALUATE

{question_content}

## OUTPUT FORMAT

```json
{{
  "question_type": "apgov_quantitative",
  "issues": [...],
  "dimensions": {{...}},
  "overall_assessment": "PASS or FAIL"
}}
```
'''

APGOV_SCOTUS_PROMPT = '''You are an expert AP Government curriculum evaluator. Evaluate this SCOTUS Comparison FRQ.

## CURRICULUM CONTEXT
{curriculum_context}

## SCOTUS COMPARISON REQUIREMENTS

Structure:
- Non-required Supreme Court case presented with facts
- Students compare with a required foundational case
- Tests understanding of constitutional principles

Required Cases: Marbury v. Madison, McCulloch v. Maryland, Schenck v. US, Brown v. Board,
Engel v. Vitale, Baker v. Carr, Gideon v. Wainwright, Tinker v. Des Moines,
NY Times v. US, Wisconsin v. Yoder, Roe v. Wade, Shaw v. Reno, US v. Lopez,
McDonald v. Chicago, Citizens United v. FEC

## EVALUATION DIMENSIONS

**case_accuracy** (0.0 or 1.0): Non-required case facts are accurate
**required_case_relevance** (0.0 or 1.0): Clear connection to a required case
**constitutional_principle** (0.0 or 1.0): Tests understanding of legal principles
**comparison_validity** (0.0 or 1.0): Meaningful comparison is possible

## CONTENT TO EVALUATE

{question_content}

## OUTPUT FORMAT

```json
{{
  "question_type": "apgov_scotus",
  "case_analysis": {{
    "non_required_case": "...",
    "relevant_required_case": "...",
    "constitutional_principle": "..."
  }},
  "issues": [...],
  "dimensions": {{...}},
  "overall_assessment": "PASS or FAIL"
}}
```
'''

APGOV_ARGUMENT_ESSAY_PROMPT = '''You are an expert AP Government curriculum evaluator. Evaluate this Argument Essay FRQ.

## CURRICULUM CONTEXT
{curriculum_context}

## ARGUMENT ESSAY REQUIREMENTS (6 Points)

Structure:
- Argumentative prompt requiring thesis
- Must allow use of foundational documents
- 6-point rubric

Official Rubric:
| Category | Points | Requirement |
|----------|--------|-------------|
| Thesis/Claim | 0-1 | Defensible claim establishing line of reasoning |
| Evidence | 0-3 | Uses specific evidence from foundational docs and course concepts |
| Reasoning | 0-1 | Explains relationship between evidence and argument |
| Rebuttal | 0-1 | Responds to opposing perspective with refutation |

Foundational Documents: Declaration of Independence, Articles of Confederation,
Constitution, Federalist 10/51/70/78, Brutus No. 1, Letter from Birmingham Jail

## EVALUATION DIMENSIONS

**prompt_arguability** (0.0 or 1.0): Requires argumentative thesis with multiple positions
**document_applicability** (0.0 or 1.0): Foundational documents are relevant
**evidence_accessibility** (0.0 or 1.0): Students can cite specific evidence
**rebuttal_opportunity** (0.0 or 1.0): Clear opposing perspectives exist

## CONTENT TO EVALUATE

{question_content}

## OUTPUT FORMAT

```json
{{
  "question_type": "apgov_argument_essay",
  "issues": [...],
  "dimensions": {{...}},
  "rubric_feasibility": {{
    "thesis_point": "...",
    "evidence_points": "...",
    "reasoning_point": "...",
    "rebuttal_point": "..."
  }},
  "overall_assessment": "PASS or FAIL"
}}
```
'''

# =============================================================================
# AP Human Geography FRQ Types
# =============================================================================

APHG_FRQ_PROMPT = '''You are an expert AP Human Geography curriculum evaluator. Evaluate this FRQ.

## CURRICULUM CONTEXT
{curriculum_context}

## AP HUMAN GEOGRAPHY FRQ REQUIREMENTS

Structure:
- FRQ Type 1: No stimulus (pure knowledge)
- FRQ Type 2: One stimulus (map, image, data)
- FRQ Type 3: Two stimuli (comparison/synthesis)
- Each FRQ worth 7 points
- Uses specific task verbs: identify, define, describe, explain, compare

## EVALUATION DIMENSIONS

**stimulus_quality** (0.0 or 1.0): Clear, readable, geographically accurate (if applicable)
**geographic_concept** (0.0 or 1.0): Tests specific APHG concepts/models
**part_clarity** (0.0 or 1.0): Each part has clear task verb
**spatial_thinking** (0.0 or 1.0): Requires geographic reasoning about space/place
**scale_appropriateness** (0.0 or 1.0): Appropriate geographic scale

## CONTENT TO EVALUATE

{question_content}

## OUTPUT FORMAT

```json
{{
  "question_type": "aphg_frq",
  "frq_subtype": "type1|type2|type3",
  "stimulus_count": 0,
  "issues": [...],
  "dimensions": {{...}},
  "overall_assessment": "PASS or FAIL"
}}
```
'''

# =============================================================================
# Helper Functions
# =============================================================================

def get_evaluation_prompt(question_type: str, curriculum_context: str, question_content: str) -> str:
    """
    Get the appropriate evaluation prompt for a question type.

    Args:
        question_type: One of: mcq, saq, dbq, leq, apgov_concept, apgov_quant,
                       apgov_scotus, apgov_argument, aphg_frq
        curriculum_context: Dynamic curriculum context
        question_content: The content to evaluate

    Returns:
        Complete evaluation prompt
    """
    prompts = {
        'mcq': MCQ_EVALUATION_PROMPT,
        'saq': SAQ_EVALUATION_PROMPT,
        'dbq': DBQ_EVALUATION_PROMPT,
        'leq': LEQ_EVALUATION_PROMPT,
        'apgov_concept': APGOV_CONCEPT_APPLICATION_PROMPT,
        'apgov_quant': APGOV_QUANTITATIVE_PROMPT,
        'apgov_scotus': APGOV_SCOTUS_PROMPT,
        'apgov_argument': APGOV_ARGUMENT_ESSAY_PROMPT,
        'aphg_frq': APHG_FRQ_PROMPT,
    }

    template = prompts.get(question_type, MCQ_EVALUATION_PROMPT)
    return template.format(
        curriculum_context=curriculum_context,
        question_content=question_content
    )


# Question types by course
COURSE_QUESTION_TYPES = {
    'APUSH': ['mcq', 'saq', 'dbq', 'leq'],
    'APWH': ['mcq', 'saq', 'dbq', 'leq'],
    'APEH': ['mcq', 'saq', 'dbq', 'leq'],
    'APGOV': ['mcq', 'apgov_concept', 'apgov_quant', 'apgov_scotus', 'apgov_argument'],
    'APHG': ['mcq', 'aphg_frq'],
}


def get_valid_question_types(course: str) -> list:
    """Get valid question types for a course."""
    return COURSE_QUESTION_TYPES.get(course, ['mcq'])
