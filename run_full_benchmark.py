#!/usr/bin/env python3
"""
Full AP Benchmark: Generate + Evaluate + Save to Database

1. Samples 50+ standards from MongoDB
2. Generates all 5 question types (MCQ, MCQ Set, SAQ, LEQ, DBQ)
3. Evaluates each question against official AP rubrics
4. Saves questions and evaluations to MongoDB
"""

import asyncio
import httpx
import json
import os
import random
import time
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional
from dataclasses import dataclass, field

import anthropic

# MongoDB connection
MONGODB_URI = os.environ.get('MONGODB_URI')
if not MONGODB_URI:
    raise ValueError("MONGODB_URI environment variable is required")

from pymongo import MongoClient

# Configuration
ENDPOINT_URL = "http://192.168.1.24:8000/generate"
NUM_STANDARDS = 50
QUESTION_TYPES = ["mcq", "mcq_set", "saq", "leq", "dbq"]
DIFFICULTIES = ["easy", "medium", "hard"]
REQUEST_TIMEOUT = 180
MAX_CONCURRENT_GEN = 5
MAX_CONCURRENT_EVAL = 3

# Anthropic client for evaluation
anthropic_client = anthropic.Anthropic()

# MongoDB collections
QUESTIONS_COLLECTION = "benchmark_questions"
EVALUATIONS_COLLECTION = "benchmark_evaluations"
RUNS_COLLECTION = "benchmark_runs"


def get_db():
    """Get MongoDB database."""
    client = MongoClient(MONGODB_URI, serverSelectionTimeoutMS=10000)
    return client['ap_social_studies']


def get_random_standards(num_standards: int = 50) -> List[Dict[str, Any]]:
    """Sample random standards from MongoDB across both courses."""
    db = get_db()

    apush_count = int(num_standards * 0.6)
    apwh_count = num_standards - apush_count

    apush_facts = list(db.facts.aggregate([
        {"$match": {"course": "APUSH"}},
        {"$sample": {"size": apush_count}}
    ]))

    apwh_facts = list(db.facts.aggregate([
        {"$match": {"course": "APWH"}},
        {"$sample": {"size": apwh_count}}
    ]))

    all_facts = apush_facts + apwh_facts
    random.shuffle(all_facts)
    return all_facts


def safe_str(val):
    """Safely convert value to string."""
    if val is None:
        return ''
    if hasattr(val, 'isoformat'):
        return val.isoformat()
    return str(val)


def build_payload(fact: Dict, question_type: str, difficulty: str) -> Dict:
    """Build generation request payload."""
    node_id = fact.get('node_id', str(uuid.uuid4())[:8])

    payload = {
        "type": question_type,
        "difficulty": difficulty,
        "course": safe_str(fact.get('course', 'APUSH')),
        "unit": int(fact.get('unit', 1)) if fact.get('unit') else 1,
        "topic": safe_str(fact.get('cluster', 'General')),
        "learning_objective": safe_str(fact.get('learning_objective', '')),
        "curriculum_fact": safe_str(fact.get('statement', '')),
        "node_id": safe_str(node_id),
        "time_period": safe_str(fact.get('date', '')),
        "theme": safe_str(fact.get('theme', '')),
    }

    if question_type == "leq":
        payload["reasoning_type"] = random.choice(["causation", "comparison", "ccot"])

    return payload


def build_evaluation_prompt(question_type: str, question_data: Dict, curriculum_context: Dict) -> str:
    """Build evaluation prompt for a question type."""

    # Format question content based on type
    if question_type == "mcq":
        content = format_mcq(question_data)
    elif question_type == "mcq_set":
        content = format_mcq_set(question_data)
    elif question_type == "saq":
        content = format_saq(question_data)
    elif question_type == "leq":
        content = format_leq(question_data)
    elif question_type == "dbq":
        content = format_dbq(question_data)
    else:
        content = json.dumps(question_data, indent=2)

    # Build curriculum context string
    ctx = f"""## CURRICULUM CONTEXT

**Course:** {curriculum_context.get('course', 'APUSH')}
**Unit:** {curriculum_context.get('unit', '')}
**Topic:** {curriculum_context.get('topic', '')}
**Learning Objective:** {curriculum_context.get('learning_objective', '')}
**Time Period:** {curriculum_context.get('time_period', '')}
**Difficulty Requested:** {curriculum_context.get('difficulty', 'medium')}
"""

    # Get appropriate prompt template
    prompt = get_evaluation_prompt_template(question_type)

    return prompt.format(
        curriculum_context=ctx,
        question_content=content
    )


def format_mcq(data: Dict) -> str:
    """Format MCQ for evaluation."""
    lines = ["## MCQ QUESTION\n"]

    if data.get('stimulus'):
        stim = data['stimulus']
        lines.append("### STIMULUS")
        if isinstance(stim, dict):
            lines.append(f"**Source:** {stim.get('source', '')}")
            lines.append(f"**Date:** {stim.get('date', '')}")
            lines.append(f"\n{stim.get('content', '')}\n")
        else:
            lines.append(str(stim))

    lines.append(f"**Question:** {data.get('question', data.get('stem', ''))}\n")
    lines.append("**Options:**")

    for opt in data.get('answer_options', data.get('options', [])):
        if isinstance(opt, dict):
            lines.append(f"  {opt.get('key', '?')}) {opt.get('text', '')}")
        else:
            lines.append(f"  - {opt}")

    lines.append(f"\n**Correct Answer:** {data.get('answer', data.get('correct_answer', ''))}")
    lines.append(f"\n**Explanation:** {data.get('explanation', '')}")

    return "\n".join(lines)


def format_mcq_set(data: Dict) -> str:
    """Format MCQ Set for evaluation."""
    lines = ["## MCQ SET\n"]

    if data.get('stimulus'):
        stim = data['stimulus']
        lines.append("### STIMULUS")
        if isinstance(stim, dict):
            lines.append(f"**Type:** {stim.get('type', '')}")
            lines.append(f"**Source:** {stim.get('source', '')}")
            lines.append(f"**Date:** {stim.get('date', '')}")
            lines.append(f"\n{stim.get('content', '')}\n")
        else:
            lines.append(str(stim))

    lines.append("### QUESTIONS\n")
    for i, q in enumerate(data.get('questions', []), 1):
        lines.append(f"**Question {i}:** {q.get('question', q.get('stem', ''))}")
        for opt in q.get('answer_options', q.get('options', [])):
            if isinstance(opt, dict):
                lines.append(f"  {opt.get('key', '?')}) {opt.get('text', '')}")
        lines.append(f"  **Answer:** {q.get('answer', '')}")
        lines.append(f"  **Explanation:** {q.get('explanation', '')}\n")

    return "\n".join(lines)


def format_saq(data: Dict) -> str:
    """Format SAQ for evaluation."""
    lines = ["## SHORT ANSWER QUESTION\n"]

    if data.get('stimulus'):
        stim = data['stimulus']
        lines.append("### STIMULUS")
        if isinstance(stim, dict):
            lines.append(f"**Source:** {stim.get('source', '')}")
            lines.append(f"**Date:** {stim.get('date', '')}")
            lines.append(f"\n{stim.get('content', '')}\n")
        else:
            lines.append(str(stim))

    lines.append(f"**Prompt:** {data.get('prompt', data.get('question', ''))}\n")
    lines.append("### PARTS\n")

    for part in data.get('parts', []):
        if isinstance(part, dict):
            lines.append(f"**({part.get('letter', '?')})** {part.get('task', part.get('prompt', ''))}")
            if part.get('scoring_criteria'):
                lines.append(f"  *Scoring:* {part['scoring_criteria']}")
            if part.get('sample_response'):
                lines.append(f"  *Sample:* {part['sample_response']}")
        else:
            lines.append(f"- {part}")
        lines.append("")

    return "\n".join(lines)


def format_leq(data: Dict) -> str:
    """Format LEQ for evaluation."""
    lines = ["## LONG ESSAY QUESTION\n"]

    lines.append(f"**Prompt:** {data.get('prompt', data.get('question', ''))}\n")
    lines.append(f"**Reasoning Type:** {data.get('reasoning_type', '')}")
    lines.append(f"**Time Period:** {data.get('time_period', '')}\n")

    if data.get('thesis_positions'):
        lines.append("### POSSIBLE THESIS POSITIONS")
        for pos in data['thesis_positions']:
            lines.append(f"- {pos}")
        lines.append("")

    if data.get('suggested_evidence'):
        lines.append("### SUGGESTED EVIDENCE")
        for ev in data['suggested_evidence']:
            lines.append(f"- {ev}")
        lines.append("")

    if data.get('scoring_notes') or data.get('rubric'):
        lines.append("### SCORING GUIDE")
        lines.append(str(data.get('scoring_notes', data.get('rubric', ''))))

    return "\n".join(lines)


def format_dbq(data: Dict) -> str:
    """Format DBQ for evaluation."""
    lines = ["## DOCUMENT-BASED QUESTION\n"]

    lines.append(f"**Prompt:** {data.get('prompt', data.get('question', ''))}\n")
    lines.append(f"**Time Period:** {data.get('time_period', '')}\n")

    lines.append("### DOCUMENTS\n")
    docs = data.get('documents', [])
    lines.append(f"**Total Documents:** {len(docs)}\n")

    for i, doc in enumerate(docs, 1):
        lines.append(f"#### Document {i}")
        if isinstance(doc, dict):
            lines.append(f"**Source:** {doc.get('source', '')}")
            lines.append(f"**Author:** {doc.get('author', '')}")
            lines.append(f"**Date:** {doc.get('date', '')}")
            lines.append(f"**Type:** {doc.get('type', '')}")
            lines.append(f"\n{doc.get('content', doc.get('text', doc.get('excerpt', '')))}\n")
        else:
            lines.append(str(doc))
        lines.append("---\n")

    if data.get('suggested_outside_evidence'):
        lines.append("### SUGGESTED OUTSIDE EVIDENCE")
        for ev in data['suggested_outside_evidence']:
            lines.append(f"- {ev}")

    return "\n".join(lines)


def get_evaluation_prompt_template(question_type: str) -> str:
    """Get evaluation prompt template for question type."""

    base_instructions = """You are an expert AP Social Studies curriculum evaluator. Evaluate this {type_name} against official College Board standards.

{curriculum_context}

## EVALUATION CRITERIA

Score each dimension as EXACTLY 0.0 (FAIL) or 1.0 (PASS).

### CRITICAL DIMENSIONS (any 0.0 = question fails)
{critical_dimensions}

### NON-CRITICAL DIMENSIONS
{non_critical_dimensions}

## CONTENT TO EVALUATE

{question_content}

## OUTPUT FORMAT

Respond with valid JSON only:

```json
{{{{
  "question_type": "{type_code}",
  "passed": true,
  "overall_score": 0.85,
  "issues": [
    {{{{"id": "ISSUE1", "dimension": "...", "snippet": "...", "explanation": "...", "severity": "major|minor"}}}}
  ],
  "dimensions": {{{{
    "dimension_name": {{{{"score": 1.0, "reasoning": "..."}}}}
  }}}},
  "strengths": ["strength 1", "strength 2"],
  "improvements": ["suggestion 1", "suggestion 2"]
}}}}
```
"""

    prompts = {
        "mcq": base_instructions.format(
            type_name="Multiple Choice Question (MCQ)",
            type_code="mcq",
            critical_dimensions="""
- **factual_accuracy**: All claims historically accurate, correct answer is correct
- **answer_validity**: Exactly ONE correct answer, clearly best option
- **curriculum_alignment**: Tests the specified learning objective""",
            non_critical_dimensions="""
- **distractor_quality**: Plausible but clearly wrong, no absolutes
- **skill_alignment**: Tests AP skill (sourcing, causation, comparison)
- **explanation_quality**: Explains why correct AND why others wrong
- **clarity**: Clear wording, no ambiguity""",
            curriculum_context="{curriculum_context}",
            question_content="{question_content}"
        ),

        "mcq_set": base_instructions.format(
            type_name="MCQ Stimulus Set",
            type_code="mcq_set",
            critical_dimensions="""
- **stimulus_quality**: Historically authentic, properly attributed
- **factual_accuracy**: All answers correct, all claims accurate
- **stimulus_integration**: Questions require stimulus analysis""",
            non_critical_dimensions="""
- **question_variety**: Questions test different skills
- **distractor_quality**: Plausible distractors across all questions
- **explanation_quality**: Each question has adequate explanation
- **difficulty_progression**: Appropriate range of difficulty""",
            curriculum_context="{curriculum_context}",
            question_content="{question_content}"
        ),

        "saq": base_instructions.format(
            type_name="Short Answer Question (SAQ)",
            type_code="saq",
            critical_dimensions="""
- **structure**: Exactly 3 parts (a, b, c), each independently scorable
- **historical_specificity**: Each part requires SPECIFIC historical evidence
- **answerability**: Parts answerable with AP course content""",
            non_critical_dimensions="""
- **task_verb_clarity**: Clear task verbs (identify, describe, explain)
- **skill_alignment**: Tests causation, comparison, or contextualization
- **scoring_clarity**: Clear what earns each point
- **stimulus_integration**: If stimulus present, parts reference it""",
            curriculum_context="{curriculum_context}",
            question_content="{question_content}"
        ),

        "leq": base_instructions.format(
            type_name="Long Essay Question (LEQ)",
            type_code="leq",
            critical_dimensions="""
- **prompt_arguability**: Requires argumentative thesis, multiple valid positions
- **reasoning_type**: Clearly requires causation, comparison, OR CCOT
- **time_period_specificity**: Clear time boundaries specified""",
            non_critical_dimensions="""
- **evidence_accessibility**: Students can cite evidence from curriculum
- **thesis_flexibility**: Multiple different valid theses possible
- **complexity_opportunity**: Allows nuanced, sophisticated argument
- **rubric_alignment**: Scoring guide matches official LEQ rubric""",
            curriculum_context="{curriculum_context}",
            question_content="{question_content}"
        ),

        "dbq": base_instructions.format(
            type_name="Document-Based Question (DBQ)",
            type_code="dbq",
            critical_dimensions="""
- **document_count**: EXACTLY 7 documents (FAIL if not 7)
- **document_authenticity**: All documents historically accurate/attributed
- **document_diversity**: Multiple perspectives, mixed document types
- **prompt_arguability**: Multiple defensible thesis positions exist""",
            non_critical_dimensions="""
- **document_relevance**: All 7 documents usable for argument
- **sourcing_opportunity**: Documents allow HIPP analysis
- **outside_evidence_scope**: Clear what outside evidence applies
- **rubric_alignment**: Matches official 7-point DBQ rubric""",
            curriculum_context="{curriculum_context}",
            question_content="{question_content}"
        ),
    }

    return prompts.get(question_type, prompts["mcq"])


async def generate_question(
    client: httpx.AsyncClient,
    payload: Dict,
    semaphore: asyncio.Semaphore
) -> Optional[Dict]:
    """Generate a single question."""
    async with semaphore:
        try:
            response = await client.post(
                ENDPOINT_URL,
                json=payload,
                timeout=REQUEST_TIMEOUT
            )
            if response.status_code == 200:
                return response.json()
            else:
                print(f"\n  Generation failed: {response.status_code}")
                return None
        except Exception as e:
            print(f"\n  Generation error: {e}")
            return None


def evaluate_question_sync(question_type: str, question_data: Dict, curriculum_context: Dict) -> Dict:
    """Evaluate a question using Claude."""
    prompt = build_evaluation_prompt(question_type, question_data, curriculum_context)

    try:
        response = anthropic_client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=2000,
            messages=[{"role": "user", "content": prompt}]
        )

        # Parse JSON from response
        text = response.content[0].text

        # Extract JSON from markdown code blocks if present
        if "```json" in text:
            text = text.split("```json")[1].split("```")[0]
        elif "```" in text:
            text = text.split("```")[1].split("```")[0]

        result = json.loads(text.strip())
        result["evaluation_success"] = True
        return result

    except json.JSONDecodeError as e:
        return {
            "evaluation_success": False,
            "error": f"JSON parse error: {e}",
            "raw_response": text if 'text' in dir() else None
        }
    except Exception as e:
        return {
            "evaluation_success": False,
            "error": str(e)
        }


async def run_full_benchmark():
    """Run full generate + evaluate benchmark."""
    run_id = str(uuid.uuid4())
    db = get_db()

    print(f"\nAP Benchmark | {run_id[:8]} | {NUM_STANDARDS} standards")

    standards = get_random_standards(NUM_STANDARDS)

    tasks = []
    for i, standard in enumerate(standards):
        qtype = QUESTION_TYPES[i % len(QUESTION_TYPES)]
        difficulty = random.choice(DIFFICULTIES)
        tasks.append({
            "standard": standard,
            "type": qtype,
            "difficulty": difficulty,
            "payload": build_payload(standard, qtype, difficulty)
        })
    random.shuffle(tasks)

    generated = []
    gen_semaphore = asyncio.Semaphore(MAX_CONCURRENT_GEN)
    gen_start = time.time()

    async with httpx.AsyncClient() as client:
        gen_tasks = []
        for task in tasks:
            gen_tasks.append(generate_question(client, task["payload"], gen_semaphore))

        for i, coro in enumerate(asyncio.as_completed(gen_tasks)):
            result = await coro
            task = tasks[i]  # Note: order may differ due to as_completed

            if result:
                generated.append({
                    "task": task,
                    "question": result,
                    "generated_at": datetime.utcnow()
                })
                status = "✓"
            else:
                status = "✗"

            print(f"\rGenerating: {len(generated)}/{len(tasks)}", end="", flush=True)

    gen_time = time.time() - gen_start
    print(f"\rGenerated: {len(generated)}/{len(tasks)} in {gen_time:.0f}s")

    eval_start = time.time()
    evaluated = []

    for i, item in enumerate(generated):
        task = item["task"]
        question = item["question"]

        curriculum_context = {
            "course": task["payload"]["course"],
            "unit": task["payload"]["unit"],
            "topic": task["payload"]["topic"],
            "learning_objective": task["payload"]["learning_objective"],
            "time_period": task["payload"]["time_period"],
            "difficulty": task["payload"]["difficulty"],
        }

        # Evaluate synchronously (API rate limits)
        evaluation = evaluate_question_sync(task["type"], question, curriculum_context)

        evaluated.append({
            **item,
            "evaluation": evaluation,
            "evaluated_at": datetime.utcnow()
        })

        passed_so_far = sum(1 for e in evaluated if e["evaluation"].get("passed"))
        print(f"\rEvaluating: {i+1}/{len(generated)} | {passed_so_far} passed", end="", flush=True)

        await asyncio.sleep(0.5)

    eval_time = time.time() - eval_start
    print(f"\rEvaluated: {len(evaluated)} in {eval_time:.0f}s" + " " * 20)

    # Prepare documents for insertion
    questions_docs = []
    evaluations_docs = []

    for item in evaluated:
        question_id = str(uuid.uuid4())

        # Question document
        questions_docs.append({
            "_id": question_id,
            "run_id": run_id,
            "type": item["task"]["type"],
            "difficulty": item["task"]["difficulty"],
            "course": item["task"]["payload"]["course"],
            "unit": item["task"]["payload"]["unit"],
            "node_id": item["task"]["payload"]["node_id"],
            "topic": item["task"]["payload"]["topic"],
            "learning_objective": item["task"]["payload"]["learning_objective"],
            "question_data": item["question"],
            "generated_at": item["generated_at"],
        })

        # Evaluation document
        evaluations_docs.append({
            "_id": str(uuid.uuid4()),
            "question_id": question_id,
            "run_id": run_id,
            "type": item["task"]["type"],
            "evaluation": item["evaluation"],
            "passed": item["evaluation"].get("passed", False) if item["evaluation"].get("evaluation_success") else None,
            "overall_score": item["evaluation"].get("overall_score", 0) if item["evaluation"].get("evaluation_success") else None,
            "evaluated_at": item["evaluated_at"],
        })

    if questions_docs:
        db[QUESTIONS_COLLECTION].insert_many(questions_docs)
    if evaluations_docs:
        db[EVALUATIONS_COLLECTION].insert_many(evaluations_docs)

    # Save run summary
    passed_count = sum(1 for e in evaluations_docs if e.get("passed"))
    failed_count = sum(1 for e in evaluations_docs if e.get("passed") == False)

    run_summary = {
        "_id": run_id,
        "started_at": datetime.utcnow(),
        "endpoint": ENDPOINT_URL,
        "num_standards": NUM_STANDARDS,
        "question_types": QUESTION_TYPES,
        "total_generated": len(generated),
        "total_evaluated": len(evaluated),
        "passed": passed_count,
        "failed": failed_count,
        "pass_rate": passed_count / len(evaluated) if evaluated else 0,
        "generation_time_seconds": gen_time,
        "evaluation_time_seconds": eval_time,
        "by_type": {},
    }

    # Stats by type
    for qtype in QUESTION_TYPES:
        type_evals = [e for e in evaluations_docs if e["type"] == qtype]
        type_passed = sum(1 for e in type_evals if e.get("passed"))
        run_summary["by_type"][qtype] = {
            "total": len(type_evals),
            "passed": type_passed,
            "pass_rate": type_passed / len(type_evals) if type_evals else 0
        }

    db[RUNS_COLLECTION].insert_one(run_summary)

    print(f"\n{'─'*50}")
    print(f"RESULTS: {passed_count}/{len(evaluated)} passed ({100*passed_count/len(evaluated):.1f}%)")
    print(f"{'─'*50}")
    for qtype in QUESTION_TYPES:
        s = run_summary["by_type"].get(qtype, {})
        print(f"  {qtype:10} {s.get('passed',0):3}/{s.get('total',0):3} ({100*s.get('pass_rate',0):5.1f}%)")
    print(f"\nSaved to MongoDB: {run_id}")

    return run_id


if __name__ == "__main__":
    asyncio.run(run_full_benchmark())
