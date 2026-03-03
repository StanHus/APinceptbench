"""
Official AP Question Type Content Formatters

Formats question content for evaluation based on question type.
Each formatter produces a structured text representation suitable
for LLM evaluation against official AP rubrics.

Field names match the AP_GENERATOR_SPEC.md exactly.
"""

from typing import Any, Dict, List, Optional


def format_mcq_content(question_dict: dict) -> str:
    """
    Format MCQ for evaluation.

    Expected generator fields (from AP_GENERATOR_SPEC.md):
    - stimulus: {type, source, date, title, content}
    - question: str
    - answer_options: [{key, text}, ...]
    - answer: str (e.g., "B")
    - explanation: str
    - skill: str
    - difficulty: str
    """
    lines = []

    # Check if we have actual content
    has_content = bool(
        question_dict.get('question') or
        question_dict.get('stem') or
        question_dict.get('answer_options') or
        question_dict.get('options') or
        question_dict.get('choices')  # Generator uses 'choices' as dict
    )

    if not has_content:
        lines.append("## ERROR: NO MCQ CONTENT PROVIDED")
        lines.append("")
        lines.append("The generator did not produce MCQ content.")
        lines.append("")
        lines.append("Expected fields: question, answer_options, answer, explanation")
        lines.append("")
        lines.append(f"Received keys: {list(question_dict.keys())}")
        return "\n".join(lines)

    # Stimulus (if present)
    stimulus = question_dict.get('stimulus')
    if stimulus:
        lines.append("## STIMULUS")
        lines.append("")
        if isinstance(stimulus, dict):
            stim_type = stimulus.get('type') or stimulus.get('source_type') or ''
            if stim_type:
                lines.append(f"**Type:** {stim_type}")
            source = stimulus.get('source') or stimulus.get('source_attribution') or ''
            if source:
                lines.append(f"**Source:** {source}")
            if stimulus.get('date'):
                lines.append(f"**Date:** {stimulus['date']}")
            if stimulus.get('title'):
                lines.append(f"**Title:** {stimulus['title']}")
            content = stimulus.get('content') or stimulus.get('text') or ''
            if content:
                lines.append("")
                lines.append(content)
        else:
            lines.append(str(stimulus))
        lines.append("")

    # Question stem
    lines.append("## QUESTION")
    lines.append("")
    question_text = question_dict.get('question') or question_dict.get('stem') or ''
    lines.append(question_text)
    lines.append("")

    # Options - handle multiple formats from different generators
    lines.append("## OPTIONS")
    lines.append("")

    # Try different field names and formats
    options = question_dict.get('answer_options') or question_dict.get('options')
    choices = question_dict.get('choices')  # Generator returns dict {"A": "text", ...}

    if choices and isinstance(choices, dict):
        # Handle dict format: {"A": "text", "B": "text", "C": "text", "D": "text"}
        for key in ["A", "B", "C", "D"]:
            if key in choices:
                lines.append(f"**{key})** {choices[key]}")
    elif options:
        for opt in options:
            if isinstance(opt, dict):
                key = opt.get('key') or opt.get('letter') or '?'
                text = opt.get('text') or opt.get('content') or ''
                lines.append(f"**{key})** {text}")
            else:
                lines.append(f"- {opt}")
    else:
        lines.append("*No options provided*")
    lines.append("")

    # Correct answer
    lines.append("## CORRECT ANSWER")
    lines.append("")
    answer = question_dict.get('answer') or question_dict.get('correct_answer') or '*Not provided*'
    lines.append(f"**{answer}**")
    lines.append("")

    # Explanation
    explanation = question_dict.get('explanation') or question_dict.get('answer_explanation') or ''
    if explanation:
        lines.append("## EXPLANATION")
        lines.append("")
        lines.append(explanation)

    # Skill
    skill = question_dict.get('skill')
    if skill:
        lines.append("")
        lines.append(f"**Skill Tested:** {skill}")

    return "\n".join(lines)


def format_mcq_set_content(question_dict: dict) -> str:
    """
    Format MCQ Set (stimulus with multiple questions) for evaluation.

    Expected generator fields (from AP_GENERATOR_SPEC.md):
    - stimulus: {type, source, date, title, content}
    - questions: [{question, answer_options, answer, explanation, skill}, ...]
    """
    lines = []

    # Check for content
    has_stimulus = bool(question_dict.get('stimulus'))
    has_questions = bool(question_dict.get('questions'))

    if not has_stimulus and not has_questions:
        lines.append("## ERROR: NO MCQ SET CONTENT PROVIDED")
        lines.append("")
        lines.append("The generator did not produce MCQ Set content.")
        lines.append("")
        lines.append("Expected fields: stimulus, questions[]")
        lines.append("")
        lines.append(f"Received keys: {list(question_dict.keys())}")
        return "\n".join(lines)

    # Stimulus
    stimulus = question_dict.get('stimulus', {})
    lines.append("## STIMULUS")
    lines.append("")
    if isinstance(stimulus, dict):
        # Type - check multiple field names
        stim_type = stimulus.get('type') or stimulus.get('source_type') or ''
        if stim_type:
            lines.append(f"**Type:** {stim_type}")
        # Source/Attribution
        source = stimulus.get('source') or stimulus.get('source_attribution') or ''
        if source:
            lines.append(f"**Source:** {source}")
        if stimulus.get('date'):
            lines.append(f"**Date:** {stimulus['date']}")
        if stimulus.get('title'):
            lines.append(f"**Title:** {stimulus['title']}")
        # Content - check 'content' OR 'text'
        content = stimulus.get('content') or stimulus.get('text') or ''
        if content:
            lines.append("")
            lines.append(content)
        if not any([stim_type, source, content]):
            lines.append("*No stimulus content provided*")
    else:
        lines.append(str(stimulus) if stimulus else "*No stimulus provided*")
    lines.append("")

    # Questions
    questions = question_dict.get('questions', [])
    lines.append(f"## QUESTIONS ({len(questions)} total)")
    lines.append("")

    if not questions:
        lines.append("*No questions provided in set*")
    else:
        for i, q in enumerate(questions, 1):
            lines.append(f"### Question {i}")
            lines.append("")

            if isinstance(q, dict):
                # Question stem
                q_text = q.get('question') or q.get('stem') or '*No question text*'
                lines.append(f"**Stem:** {q_text}")
                lines.append("")

                # Options - handle multiple formats
                options = q.get('answer_options') or q.get('options')
                choices = q.get('choices')  # Generator returns dict {"A": "text", ...}

                if choices and isinstance(choices, dict):
                    # Handle dict format: {"A": "text", "B": "text", ...}
                    lines.append("**Options:**")
                    for key in ["A", "B", "C", "D"]:
                        if key in choices:
                            lines.append(f"  {key}) {choices[key]}")
                elif options:
                    lines.append("**Options:**")
                    for opt in options:
                        if isinstance(opt, dict):
                            key = opt.get('key') or opt.get('letter') or '?'
                            text = opt.get('text') or opt.get('content') or ''
                            lines.append(f"  {key}) {text}")
                        else:
                            lines.append(f"  - {opt}")
                else:
                    lines.append("**Options:** *Not provided*")
                lines.append("")

                # Answer
                answer = q.get('answer') or q.get('correct_answer') or '*Not provided*'
                lines.append(f"**Correct Answer:** {answer}")

                # Explanation
                explanation = q.get('explanation') or ''
                if explanation:
                    lines.append(f"**Explanation:** {explanation}")

                # Skill
                skill = q.get('skill') or ''
                if skill:
                    lines.append(f"**Skill:** {skill}")
            else:
                lines.append(str(q))

            lines.append("")
            lines.append("---")
            lines.append("")

    return "\n".join(lines)


def format_saq_content(question_dict: dict) -> str:
    """
    Format SAQ (Short Answer Question) for evaluation.

    Expected generator fields (from AP_GENERATOR_SPEC.md):
    - stimulus: {type, source, date, author, content} (optional)
    - prompt: str
    - parts: [{letter, task, task_verb, scoring_criteria, sample_response}, ...]
    - time_period: str
    - topic: str
    - skill: str
    """
    lines = []

    # Check for content - generator uses 'preamble' and parts dict
    has_prompt = bool(question_dict.get('prompt') or question_dict.get('question') or question_dict.get('preamble'))
    has_parts = bool(question_dict.get('parts'))

    if not has_prompt and not has_parts:
        lines.append("## ERROR: NO SAQ CONTENT PROVIDED")
        lines.append("")
        lines.append("The generator did not produce SAQ content.")
        lines.append("")
        lines.append("Expected fields: prompt, parts[{letter, task}]")
        lines.append("")
        lines.append(f"Received keys: {list(question_dict.keys())}")
        return "\n".join(lines)

    # Stimulus (if present)
    stimulus = question_dict.get('stimulus')
    if stimulus:
        lines.append("## STIMULUS")
        lines.append("")
        if isinstance(stimulus, dict):
            stim_type = stimulus.get('type') or stimulus.get('source_type') or ''
            if stim_type:
                lines.append(f"**Type:** {stim_type}")
            source = stimulus.get('source') or stimulus.get('source_attribution') or ''
            if source:
                lines.append(f"**Source:** {source}")
            if stimulus.get('date'):
                lines.append(f"**Date:** {stimulus['date']}")
            if stimulus.get('author'):
                lines.append(f"**Author:** {stimulus['author']}")
            content = stimulus.get('content') or stimulus.get('text') or ''
            if content:
                lines.append("")
                lines.append(content)
        else:
            lines.append(str(stimulus))
        lines.append("")

    # Main prompt / Preamble
    lines.append("## QUESTION PROMPT")
    lines.append("")
    # Generator may use 'preamble' instead of 'prompt'
    prompt = question_dict.get('preamble') or question_dict.get('prompt') or question_dict.get('question') or '*No prompt provided*'
    lines.append(prompt)
    lines.append("")

    # Parts - THIS IS CRITICAL FOR SAQ
    # Generator returns parts as dict: {"a": {prompt, skill, scoring_notes}, ...}
    lines.append("## PARTS")
    lines.append("")

    parts = question_dict.get('parts', {})
    part_count = 0

    if isinstance(parts, dict):
        # Handle dict format: {"a": {...}, "b": {...}, "c": {...}}
        for letter in ['a', 'b', 'c']:
            part = parts.get(letter, {})
            if part:
                part_count += 1
                if isinstance(part, dict):
                    # Get task from various possible field names
                    task = (part.get('prompt') or part.get('task') or
                           part.get('question') or '*No task specified*')
                    task_verb = part.get('task_verb') or part.get('skill') or ''

                    lines.append(f"**({letter})** {task}")

                    if task_verb:
                        lines.append(f"   *Task verb/Skill: {task_verb}*")
                    scoring = part.get('scoring_criteria') or part.get('scoring_notes') or ''
                    if scoring:
                        lines.append(f"   *Scoring: {scoring}*")
                    if part.get('sample_response'):
                        lines.append(f"   *Sample: {part['sample_response'][:100]}...*")
                else:
                    lines.append(f"**({letter})** {part}")
                lines.append("")
            else:
                lines.append(f"**({letter})** *No content for part {letter}*")
                lines.append("")
    elif isinstance(parts, list):
        # Handle list format (legacy)
        for i, part in enumerate(parts):
            letter = chr(ord('a') + i)
            part_count += 1
            if isinstance(part, dict):
                task = (part.get('task') or part.get('prompt') or
                       part.get('question') or '*No task specified*')
                task_verb = part.get('task_verb', '')

                lines.append(f"**({letter})** {task}")

                if task_verb:
                    lines.append(f"   *Task verb: {task_verb}*")
                if part.get('scoring_criteria'):
                    lines.append(f"   *Scoring: {part['scoring_criteria']}*")
            else:
                lines.append(f"**({letter})** {part}")
            lines.append("")
    else:
        lines.append("**ERROR: No parts (a), (b), (c) provided**")
        lines.append("")
        lines.append("SAQ requires exactly 3 parts.")

    # Part count verification
    lines.append(f"**Total Parts:** {part_count} (required: 3)")
    lines.append("")

    # Metadata
    if question_dict.get('time_period'):
        lines.append(f"**Time Period:** {question_dict['time_period']}")
    if question_dict.get('topic'):
        lines.append(f"**Topic:** {question_dict['topic']}")
    if question_dict.get('skill'):
        lines.append(f"**Skill:** {question_dict['skill']}")

    return "\n".join(lines)


def format_dbq_content(question_dict: dict) -> str:
    """
    Format DBQ (Document-Based Question) for evaluation.

    Expected generator fields (from AP_GENERATOR_SPEC.md):
    - prompt: str
    - time_period: str
    - topic: str
    - documents: [{number, type, source, author, date, title, context, content, perspective}, ...]
    - suggested_thesis_positions: [str, ...]
    - suggested_outside_evidence: [str, ...]
    """
    lines = []

    # Check for critical content
    has_prompt = bool(question_dict.get('prompt') or question_dict.get('question'))
    has_documents = bool(question_dict.get('documents'))

    if not has_prompt:
        lines.append("## ERROR: NO DBQ PROMPT PROVIDED")
        lines.append("")

    if not has_documents:
        lines.append("## ERROR: NO DOCUMENTS PROVIDED")
        lines.append("")
        lines.append("DBQ requires exactly 7 documents.")
        lines.append("")
        lines.append(f"Received keys: {list(question_dict.keys())}")
        if not has_prompt:
            return "\n".join(lines)
        lines.append("")

    # Prompt
    lines.append("## DBQ PROMPT")
    lines.append("")
    prompt = question_dict.get('prompt') or question_dict.get('question') or '*No prompt provided*'
    lines.append(prompt)
    lines.append("")

    # Time period
    if question_dict.get('time_period'):
        lines.append(f"**Time Period:** {question_dict['time_period']}")
        lines.append("")
    if question_dict.get('topic'):
        lines.append(f"**Topic:** {question_dict['topic']}")
        lines.append("")

    # Documents
    lines.append("## DOCUMENTS")
    lines.append("")

    documents = question_dict.get('documents', [])

    if not documents:
        lines.append("**CRITICAL ERROR: No documents provided**")
        lines.append("")
        lines.append("A DBQ must include exactly 7 documents.")
    else:
        for i, doc in enumerate(documents, 1):
            doc_num = doc.get('number', i) if isinstance(doc, dict) else i
            lines.append(f"### Document {doc_num}")
            lines.append("")

            if isinstance(doc, dict):
                # Attribution - REQUIRED for DBQ
                if doc.get('source'):
                    lines.append(f"**Source:** {doc['source']}")
                if doc.get('author'):
                    lines.append(f"**Author:** {doc['author']}")
                if doc.get('date'):
                    lines.append(f"**Date:** {doc['date']}")
                if doc.get('type'):
                    lines.append(f"**Type:** {doc['type']}")
                if doc.get('title'):
                    lines.append(f"**Title:** {doc['title']}")
                if doc.get('context'):
                    lines.append(f"**Context:** {doc['context']}")
                if doc.get('perspective'):
                    lines.append(f"**Perspective:** {doc['perspective']}")

                lines.append("")

                # Content
                content = (doc.get('content') or doc.get('text') or
                          doc.get('excerpt') or '*No content provided*')
                lines.append(content)
            else:
                lines.append(str(doc))

            lines.append("")
            lines.append("---")
            lines.append("")

    # Document count - CRITICAL CHECK
    lines.append(f"**Total Documents:** {len(documents)} (required: 7)")
    if len(documents) != 7:
        lines.append("")
        lines.append("**⚠️ CRITICAL: DBQ must have exactly 7 documents**")
    lines.append("")

    # Suggested elements (for verification)
    thesis_positions = question_dict.get('suggested_thesis_positions', [])
    if thesis_positions:
        lines.append("## SUGGESTED THESIS POSITIONS")
        lines.append("")
        for pos in thesis_positions:
            lines.append(f"- {pos}")
        lines.append("")

    outside_evidence = question_dict.get('suggested_outside_evidence', [])
    if outside_evidence:
        lines.append("## SUGGESTED OUTSIDE EVIDENCE")
        lines.append("")
        for ev in outside_evidence:
            lines.append(f"- {ev}")
        lines.append("")

    return "\n".join(lines)


def format_leq_content(question_dict: dict) -> str:
    """
    Format LEQ (Long Essay Question) for evaluation.

    Expected generator fields (from AP_GENERATOR_SPEC.md):
    - prompt: str
    - time_period: str
    - reasoning_type: "causation"|"comparison"|"continuity_and_change"
    - topic: str
    - thesis_positions: [str, ...]
    - suggested_evidence: [str, ...]
    """
    lines = []

    # Check for content
    has_prompt = bool(question_dict.get('prompt') or question_dict.get('question'))

    if not has_prompt:
        lines.append("## ERROR: NO LEQ PROMPT PROVIDED")
        lines.append("")
        lines.append("The generator did not produce LEQ content.")
        lines.append("")
        lines.append(f"Received keys: {list(question_dict.keys())}")
        return "\n".join(lines)

    # Prompt
    lines.append("## LEQ PROMPT")
    lines.append("")
    prompt = question_dict.get('prompt') or question_dict.get('question') or ''
    lines.append(prompt)
    lines.append("")

    # Reasoning type - CRITICAL for LEQ
    reasoning_type = question_dict.get('reasoning_type') or question_dict.get('skill') or ''
    if reasoning_type:
        lines.append(f"**Historical Reasoning Type:** {reasoning_type}")
        lines.append("")
    else:
        lines.append("**⚠️ WARNING: No reasoning type specified**")
        lines.append("LEQ must specify: causation, comparison, or continuity_and_change (CCOT)")
        lines.append("")

    # Time period
    time_period = question_dict.get('time_period') or ''
    if time_period:
        lines.append(f"**Time Period:** {time_period}")
        lines.append("")

    # Topic/Theme
    topic = question_dict.get('topic') or question_dict.get('theme') or ''
    if topic:
        lines.append(f"**Topic/Theme:** {topic}")
        lines.append("")

    # Thesis positions
    theses = question_dict.get('thesis_positions') or question_dict.get('arguable_positions') or []
    if theses:
        lines.append("## POSSIBLE THESIS POSITIONS")
        lines.append("")
        for thesis in theses:
            lines.append(f"- {thesis}")
        lines.append("")

    # Suggested evidence
    evidence = question_dict.get('suggested_evidence') or question_dict.get('evidence') or []
    if evidence:
        lines.append("## SUGGESTED EVIDENCE")
        lines.append("")
        if isinstance(evidence, list):
            for ev in evidence:
                lines.append(f"- {ev}")
        else:
            lines.append(str(evidence))
        lines.append("")

    # Complexity opportunities
    complexity = question_dict.get('complexity_opportunities') or []
    if complexity:
        lines.append("## COMPLEXITY OPPORTUNITIES")
        lines.append("")
        for c in complexity:
            lines.append(f"- {c}")
        lines.append("")

    return "\n".join(lines)


def format_apgov_concept_application_content(question_dict: dict) -> str:
    """Format AP Gov Concept Application FRQ."""
    lines = []

    # Scenario
    lines.append("## POLITICAL SCENARIO")
    lines.append("")
    scenario = question_dict.get('scenario') or question_dict.get('stimulus') or '*No scenario provided*'
    lines.append(scenario)
    lines.append("")

    # Parts
    lines.append("## QUESTION PARTS")
    lines.append("")

    parts = question_dict.get('parts', [])
    if parts:
        for i, part in enumerate(parts):
            letter = chr(ord('a') + i)
            if isinstance(part, dict):
                task = part.get('task') or part.get('prompt') or ''
                lines.append(f"**({letter})** {task}")
                if part.get('points'):
                    lines.append(f"   *({part['points']} point(s))*")
            else:
                lines.append(f"**({letter})** {part}")
            lines.append("")
    else:
        lines.append("*No parts provided*")

    # Concepts tested
    concepts = question_dict.get('concepts_tested') or question_dict.get('concepts') or []
    if concepts:
        lines.append("## CONCEPTS TESTED")
        lines.append("")
        for c in concepts:
            lines.append(f"- {c}")
        lines.append("")

    return "\n".join(lines)


def format_apgov_quantitative_content(question_dict: dict) -> str:
    """Format AP Gov Quantitative Analysis FRQ."""
    lines = []

    # Data/Visual
    lines.append("## DATA VISUALIZATION")
    lines.append("")
    data = question_dict.get('data') or question_dict.get('chart') or question_dict.get('stimulus') or {}
    if isinstance(data, dict):
        if data.get('title'):
            lines.append(f"**Title:** {data['title']}")
        if data.get('type'):
            lines.append(f"**Type:** {data['type']}")
        if data.get('source'):
            lines.append(f"**Source:** {data['source']}")
        if data.get('description'):
            lines.append("")
            lines.append(data['description'])
        if data.get('values'):
            lines.append("")
            lines.append("**Data:**")
            lines.append(str(data['values']))
    else:
        lines.append(str(data) if data else "*No data provided*")
    lines.append("")

    # Parts
    lines.append("## QUESTION PARTS")
    lines.append("")
    parts = question_dict.get('parts', [])
    for i, part in enumerate(parts):
        letter = chr(ord('a') + i)
        if isinstance(part, dict):
            task = part.get('task') or part.get('prompt') or ''
            lines.append(f"**({letter})** {task}")
        else:
            lines.append(f"**({letter})** {part}")
        lines.append("")

    return "\n".join(lines)


def format_apgov_scotus_content(question_dict: dict) -> str:
    """Format AP Gov SCOTUS Comparison FRQ."""
    lines = []

    # Non-required case
    lines.append("## NON-REQUIRED CASE")
    lines.append("")
    case = question_dict.get('non_required_case') or question_dict.get('case') or {}
    if isinstance(case, dict):
        if case.get('name'):
            lines.append(f"**Case:** {case['name']}")
        if case.get('year'):
            lines.append(f"**Year:** {case['year']}")
        if case.get('facts'):
            lines.append("")
            lines.append("**Facts:**")
            lines.append(case['facts'])
        if case.get('ruling'):
            lines.append("")
            lines.append("**Ruling:**")
            lines.append(case['ruling'])
        if case.get('constitutional_issue'):
            lines.append("")
            lines.append(f"**Constitutional Issue:** {case['constitutional_issue']}")
    else:
        lines.append(str(case) if case else "*No case provided*")
    lines.append("")

    # Parts
    lines.append("## QUESTION PARTS")
    lines.append("")
    parts = question_dict.get('parts', [])
    for i, part in enumerate(parts):
        letter = chr(ord('a') + i)
        if isinstance(part, dict):
            task = part.get('task') or part.get('prompt') or ''
            lines.append(f"**({letter})** {task}")
        else:
            lines.append(f"**({letter})** {part}")
        lines.append("")

    # Required case reference
    required = question_dict.get('relevant_required_cases') or question_dict.get('required_case') or []
    if required:
        lines.append("## RELEVANT REQUIRED CASES")
        lines.append("")
        if isinstance(required, list):
            for r in required:
                lines.append(f"- {r}")
        else:
            lines.append(f"- {required}")
        lines.append("")

    return "\n".join(lines)


def format_apgov_argument_essay_content(question_dict: dict) -> str:
    """Format AP Gov Argument Essay FRQ."""
    lines = []

    # Prompt
    lines.append("## ARGUMENT ESSAY PROMPT")
    lines.append("")
    prompt = question_dict.get('prompt') or question_dict.get('question') or '*No prompt provided*'
    lines.append(prompt)
    lines.append("")

    # Foundational documents
    docs = question_dict.get('foundational_documents') or question_dict.get('required_documents') or []
    if docs:
        lines.append("## RELEVANT FOUNDATIONAL DOCUMENTS")
        lines.append("")
        for doc in docs:
            lines.append(f"- {doc}")
        lines.append("")

    # Thesis positions
    positions = question_dict.get('thesis_positions') or []
    if positions:
        lines.append("## POSSIBLE POSITIONS")
        lines.append("")
        for pos in positions:
            lines.append(f"- {pos}")
        lines.append("")

    # Suggested evidence
    evidence = question_dict.get('suggested_evidence') or []
    if evidence:
        lines.append("## SUGGESTED EVIDENCE")
        lines.append("")
        for ev in evidence:
            lines.append(f"- {ev}")
        lines.append("")

    return "\n".join(lines)


def format_aphg_frq_content(question_dict: dict) -> str:
    """Format AP Human Geography FRQ."""
    lines = []

    # FRQ Type
    frq_type = question_dict.get('frq_subtype') or question_dict.get('frq_type') or 'type1'
    lines.append(f"## AP HUMAN GEOGRAPHY FRQ ({frq_type.upper()})")
    lines.append("")

    # Stimuli (if present)
    stimuli = question_dict.get('stimuli') or question_dict.get('stimulus') or []
    if stimuli:
        if not isinstance(stimuli, list):
            stimuli = [stimuli]
        lines.append("## STIMULI")
        lines.append("")
        for i, stim in enumerate(stimuli, 1):
            lines.append(f"### Stimulus {i}")
            if isinstance(stim, dict):
                if stim.get('type'):
                    lines.append(f"**Type:** {stim['type']}")
                if stim.get('title'):
                    lines.append(f"**Title:** {stim['title']}")
                if stim.get('description'):
                    lines.append("")
                    lines.append(stim['description'])
            else:
                lines.append(str(stim))
            lines.append("")

    # Question
    lines.append("## QUESTION")
    lines.append("")
    question = question_dict.get('question') or question_dict.get('prompt') or '*No question provided*'
    lines.append(question)
    lines.append("")

    # Parts
    lines.append("## PARTS")
    lines.append("")
    parts = question_dict.get('parts', [])
    for i, part in enumerate(parts):
        letter = chr(ord('A') + i)  # APHG uses A, B, C...
        if isinstance(part, dict):
            task = part.get('task') or part.get('prompt') or ''
            points = part.get('points', 1)
            lines.append(f"**{letter}.** {task} *({points} point)*")
        else:
            lines.append(f"**{letter}.** {part}")
        lines.append("")

    # Concepts/Models
    concepts = question_dict.get('concepts') or question_dict.get('models') or []
    if concepts:
        lines.append("## GEOGRAPHIC CONCEPTS/MODELS")
        lines.append("")
        for c in concepts:
            lines.append(f"- {c}")
        lines.append("")

    return "\n".join(lines)


def format_question_content(question_dict: dict, question_type: str) -> str:
    """
    Format question content based on type.

    Args:
        question_dict: The question data from generator
        question_type: One of: mcq, mcq_set, saq, dbq, leq,
                       apgov_concept_application, apgov_quantitative,
                       apgov_scotus, apgov_argument, aphg_frq

    Returns:
        Formatted string for evaluation
    """
    # Normalize question type
    qtype = question_type.lower().replace('-', '_')

    formatters = {
        'mcq': format_mcq_content,
        'mcq_set': format_mcq_set_content,
        'saq': format_saq_content,
        'dbq': format_dbq_content,
        'leq': format_leq_content,
        'apgov_concept_application': format_apgov_concept_application_content,
        'apgov_concept': format_apgov_concept_application_content,
        'apgov_quantitative': format_apgov_quantitative_content,
        'apgov_quant': format_apgov_quantitative_content,
        'apgov_scotus': format_apgov_scotus_content,
        'apgov_argument': format_apgov_argument_essay_content,
        'aphg_frq': format_aphg_frq_content,
    }

    formatter = formatters.get(qtype)

    if formatter is None:
        # Return debug info for unknown type
        lines = [
            f"## UNKNOWN QUESTION TYPE: {question_type}",
            "",
            f"Available types: {list(formatters.keys())}",
            "",
            f"Question dict keys: {list(question_dict.keys())}",
            "",
            "## RAW CONTENT",
            "",
            str(question_dict)[:2000]
        ]
        return "\n".join(lines)

    return formatter(question_dict)
