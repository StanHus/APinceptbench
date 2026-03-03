#!/usr/bin/env python3
"""
Official AP Benchmark - Ironclad Evaluator

Uses official AP rubrics from College Board. The evaluator is FIXED and does not
adapt to generator output. Questions either meet AP standards or they don't.

Collections:
- benchmark_questions: Raw generated questions
- benchmark_evaluations: Evaluation results with rubric scores
- benchmark_runs: Run summaries and statistics
"""

import asyncio
import json
import os
import random
import time
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

import anthropic
import httpx
from pymongo import MongoClient

# Load official AP prompts
from ap_benchmark.prompts.official_ap_prompts import (
    MCQ_EVALUATION_PROMPT,
    MCQ_SET_EVALUATION_PROMPT,
    SAQ_EVALUATION_PROMPT,
    DBQ_EVALUATION_PROMPT,
    LEQ_EVALUATION_PROMPT,
    PROMPT_VERSION,
)
from ap_benchmark.prompts.official_ap_formatters import format_question_content

# Configuration
MONGODB_URI = os.environ.get('MONGODB_URI')
if not MONGODB_URI:
    raise ValueError("MONGODB_URI environment variable is required")
ENDPOINT_URL = "http://192.168.1.24:8000/generate"
NUM_STANDARDS = 20
QUESTIONS_PER_STANDARD = 3
QUESTION_TYPES = ["mcq", "mcq_set", "saq", "leq", "dbq"]
DIFFICULTIES = ["easy", "medium", "hard"]
REQUEST_TIMEOUT = 180
MAX_CONCURRENT_GEN = 8  # Increased for larger batch

# Anthropic client
anthropic_client = anthropic.Anthropic()

# MongoDB collections
DB_NAME = "ap_social_studies"
QUESTIONS_COL = "benchmark_questions"
EVALUATIONS_COL = "benchmark_evaluations"
RUNS_COL = "benchmark_runs"


def get_db():
    """Get MongoDB database."""
    client = MongoClient(MONGODB_URI, serverSelectionTimeoutMS=10000)
    return client[DB_NAME]


def get_random_standards(num: int) -> List[Dict]:
    """Sample random standards from both courses."""
    db = get_db()

    # 60% APUSH, 40% APWH
    apush_count = int(num * 0.6)
    apwh_count = num - apush_count

    apush = list(db.facts.aggregate([
        {"$match": {"course": "APUSH"}},
        {"$sample": {"size": apush_count}}
    ]))

    apwh = list(db.facts.aggregate([
        {"$match": {"course": "APWH"}},
        {"$sample": {"size": apwh_count}}
    ]))

    standards = apush + apwh
    random.shuffle(standards)

    return standards


def safe_str(val) -> str:
    """Convert any value to string safely."""
    if val is None:
        return ""
    if hasattr(val, 'isoformat'):
        return val.isoformat()
    return str(val)


def build_generation_payload(fact: Dict, qtype: str, difficulty: str) -> Dict:
    """Build payload for question generation."""
    return {
        "type": qtype,
        "difficulty": difficulty,
        "course": safe_str(fact.get("course", "APUSH")),
        "unit": int(fact.get("unit", 1)) if fact.get("unit") else 1,
        "topic": safe_str(fact.get("cluster", "")),
        "learning_objective": safe_str(fact.get("learning_objective", "")),
        "curriculum_fact": safe_str(fact.get("statement", "")),
        "node_id": safe_str(fact.get("node_id", "")),
        "time_period": safe_str(fact.get("date", "")),
        "theme": safe_str(fact.get("theme", "")),
        "reasoning_type": random.choice(["causation", "comparison", "ccot"]) if qtype == "leq" else None,
    }


def build_curriculum_context(payload: Dict) -> str:
    """Build curriculum context for evaluation."""
    return f"""**Course:** {payload.get('course', 'APUSH')}
**Unit:** {payload.get('unit', '')}
**Topic:** {payload.get('topic', '')}
**Learning Objective:** {payload.get('learning_objective', '')}
**Time Period:** {payload.get('time_period', '')}
**Requested Difficulty:** {payload.get('difficulty', 'medium')}
**Theme:** {payload.get('theme', '')}"""


def get_evaluation_prompt(qtype: str) -> str:
    """Get the official evaluation prompt for a question type."""
    prompts = {
        "mcq": MCQ_EVALUATION_PROMPT,
        "mcq_set": MCQ_SET_EVALUATION_PROMPT,  # Dedicated prompt for stimulus-based sets
        "saq": SAQ_EVALUATION_PROMPT,
        "leq": LEQ_EVALUATION_PROMPT,
        "dbq": DBQ_EVALUATION_PROMPT,
    }
    return prompts.get(qtype, MCQ_EVALUATION_PROMPT)


def evaluate_question(qtype: str, question_data: Dict, curriculum_context: str) -> Dict:
    """
    Evaluate a question using the official AP rubric.

    This is the IRONCLAD evaluator - it does not adapt to generator output.
    """
    # Extract actual question content from generator response structure
    # Generator returns: {success, request, output, generation_time_ms}
    if "output" in question_data:
        actual_content = question_data["output"]
    else:
        actual_content = question_data

    # Get official prompt template
    prompt_template = get_evaluation_prompt(qtype)

    # Format question content using official formatter
    question_content = format_question_content(actual_content, qtype)

    # Build full evaluation prompt
    full_prompt = prompt_template.format(
        curriculum_context=curriculum_context,
        question_content=question_content
    )

    try:
        response = anthropic_client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=8000,
            messages=[{"role": "user", "content": full_prompt}]
        )

        text = response.content[0].text

        # Extract JSON from response
        if "```json" in text:
            json_str = text.split("```json")[1].split("```")[0]
        elif "```" in text:
            json_str = text.split("```")[1].split("```")[0]
        else:
            json_str = text

        result = json.loads(json_str.strip())

        # Calculate overall score
        dimensions = result.get("dimensions", {})
        scores = []
        for dim_data in dimensions.values():
            if isinstance(dim_data, dict):
                scores.append(dim_data.get("score", 0))
            else:
                scores.append(float(dim_data) if dim_data else 0)

        overall_score = sum(scores) / len(scores) if scores else 0

        # HARD FAIL dimensions - structural requirements that MUST pass
        # These are non-negotiable structural issues
        hard_fail_dims = {
            "document_count",      # DBQ must have exactly 7 documents
            "prompt_structure",    # SAQ must have 3 parts (a, b, c)
            "factual_accuracy",    # Cannot have factual errors
            "answer_validity",     # MCQ must have exactly 1 correct answer
        }

        # Check for hard failures
        critical_failed = False
        for dim_name in hard_fail_dims:
            if dim_name in dimensions:
                dim_data = dimensions[dim_name]
                score = dim_data.get("score", 1.0) if isinstance(dim_data, dict) else dim_data
                if score < 1.0:
                    critical_failed = True
                    break

        # Pass if: no hard failures AND overall score >= 0.70
        passed = not critical_failed and overall_score >= 0.70

        return {
            "success": True,
            "passed": passed,
            "overall_score": overall_score,
            "critical_failed": critical_failed,
            "dimensions": dimensions,
            "issues": result.get("issues", []),
            "overall_assessment": result.get("overall_assessment", ""),
            "evaluator_version": PROMPT_VERSION,
        }

    except json.JSONDecodeError as e:
        return {
            "success": False,
            "error": f"JSON parse error: {str(e)}",
            "raw_response": text if 'text' in dir() else None,
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
        }


async def generate_question(client: httpx.AsyncClient, payload: Dict, sem: asyncio.Semaphore) -> Optional[Dict]:
    """Generate a question from the endpoint."""
    async with sem:
        try:
            resp = await client.post(ENDPOINT_URL, json=payload, timeout=REQUEST_TIMEOUT)
            if resp.status_code == 200:
                return resp.json()
            return None
        except Exception as e:
            print(f"\n  Gen error: {e}")
            return None


async def run_benchmark():
    """Run the full benchmark: generate, evaluate, save."""
    run_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc)
    db = get_db()

    print(f"\nAP Benchmark | {run_id[:8]} | {NUM_STANDARDS} standards × {QUESTIONS_PER_STANDARD} = {NUM_STANDARDS * QUESTIONS_PER_STANDARD} questions")

    # Sample standards
    standards = get_random_standards(NUM_STANDARDS)

    # Create tasks - generate QUESTIONS_PER_STANDARD questions per standard
    # Each standard gets different question types
    tasks = []
    type_idx = 0
    for std in standards:
        for q in range(QUESTIONS_PER_STANDARD):
            qtype = QUESTION_TYPES[type_idx % len(QUESTION_TYPES)]
            type_idx += 1
            diff = random.choice(DIFFICULTIES)
            payload = build_generation_payload(std, qtype, diff)
            tasks.append({"standard": std, "type": qtype, "difficulty": diff, "payload": payload})

    random.shuffle(tasks)

    generated = []
    gen_failed_tasks = []  # Track failed generations
    sem = asyncio.Semaphore(MAX_CONCURRENT_GEN)
    gen_start = time.time()

    async with httpx.AsyncClient() as client:
        # Use gather to preserve order - results[i] corresponds to tasks[i]
        async def gen_with_index(idx: int, task: Dict) -> tuple:
            result = await generate_question(client, task["payload"], sem)
            return (idx, result)

        coros = [gen_with_index(i, t) for i, t in enumerate(tasks)]

        # Process as they complete but track by index
        for coro in asyncio.as_completed(coros):
            idx, result = await coro
            if result:
                # Match result to its original task by index
                generated.append({"task": tasks[idx], "question": result})
            else:
                # Track failed generations
                gen_failed_tasks.append(tasks[idx])

            print(f"\rGenerating: {len(generated)}/{len(tasks)}", end="", flush=True)

    gen_time = time.time() - gen_start
    gen_errors = len(gen_failed_tasks)
    print(f"\rGenerated: {len(generated)}/{len(tasks)} ({gen_errors} errors) in {gen_time:.0f}s")

    eval_start = time.time()
    results = []

    for i, item in enumerate(generated):
        task = item["task"]
        question = item["question"]

        ctx = build_curriculum_context(task["payload"])
        evaluation = evaluate_question(task["type"], question, ctx)

        results.append({
            "task": task,
            "question": question,
            "evaluation": evaluation,
        })

        if evaluation.get("success"):
            status = "✓" if evaluation.get("passed") else "✗"
            score = evaluation.get("overall_score", 0)
        else:
            status = "?"
            score = 0

        passed_so_far = sum(1 for r in results if r["evaluation"].get("passed"))
        print(f"\rEvaluating: {i+1}/{len(generated)} | {passed_so_far} passed", end="", flush=True)

        await asyncio.sleep(0.3)  # Rate limiting

    eval_time = time.time() - eval_start
    print(f"\rEvaluated: {len(results)} in {eval_time:.0f}s" + " " * 20)

    questions_to_save = []
    evaluations_to_save = []

    for r in results:
        qid = str(uuid.uuid4())

        questions_to_save.append({
            "_id": qid,
            "run_id": run_id,
            "type": r["task"]["type"],
            "difficulty": r["task"]["difficulty"],
            "course": r["task"]["payload"]["course"],
            "unit": r["task"]["payload"]["unit"],
            "node_id": r["task"]["payload"]["node_id"],
            "topic": r["task"]["payload"]["topic"],
            "learning_objective": r["task"]["payload"]["learning_objective"],
            "question_data": r["question"],
            "created_at": now,
        })

        evaluations_to_save.append({
            "_id": str(uuid.uuid4()),
            "question_id": qid,
            "run_id": run_id,
            "type": r["task"]["type"],
            "passed": r["evaluation"].get("passed"),
            "overall_score": r["evaluation"].get("overall_score"),
            "critical_failed": r["evaluation"].get("critical_failed"),
            "dimensions": r["evaluation"].get("dimensions"),
            "issues": r["evaluation"].get("issues"),
            "evaluation_success": r["evaluation"].get("success"),
            "evaluator_version": PROMPT_VERSION,
            "created_at": now,
        })

    if questions_to_save:
        db[QUESTIONS_COL].insert_many(questions_to_save)

    if evaluations_to_save:
        db[EVALUATIONS_COL].insert_many(evaluations_to_save)

    # Calculate statistics (generation failures count as 0s)
    passed = sum(1 for e in evaluations_to_save if e.get("passed"))
    eval_failed = sum(1 for e in evaluations_to_save if e.get("passed") == False)
    failed = eval_failed + gen_errors  # Include generation failures

    # Count generation failures by type
    gen_failed_by_type = {}
    for task in gen_failed_tasks:
        qtype = task["type"]
        gen_failed_by_type[qtype] = gen_failed_by_type.get(qtype, 0) + 1

    by_type = {}
    for qtype in QUESTION_TYPES:
        type_evals = [e for e in evaluations_to_save if e["type"] == qtype]
        type_passed = sum(1 for e in type_evals if e.get("passed"))
        type_gen_failed = gen_failed_by_type.get(qtype, 0)
        type_total = len(type_evals) + type_gen_failed
        by_type[qtype] = {
            "total": type_total,
            "passed": type_passed,
            "gen_failed": type_gen_failed,
            "rate": type_passed / type_total if type_total else 0
        }

    by_course = {}
    for course in ["APUSH", "APWH"]:
        course_evals = [e for e in evaluations_to_save if questions_to_save[[q["_id"] for q in questions_to_save].index(e["question_id"])]["course"] == course]
        course_passed = sum(1 for e in course_evals if e.get("passed"))
        by_course[course] = {
            "total": len(course_evals),
            "passed": course_passed,
            "rate": course_passed / len(course_evals) if course_evals else 0
        }

    # Save run summary
    total_questions = len(tasks)  # Total attempted (includes gen failures)
    run_doc = {
        "_id": run_id,
        "started_at": now,
        "evaluator_version": PROMPT_VERSION,
        "endpoint": ENDPOINT_URL,
        "standards_sampled": len(standards),
        "total_attempted": total_questions,
        "generated": len(generated),
        "generation_failures": gen_errors,
        "evaluated": len(results),
        "passed": passed,
        "failed": failed,
        "pass_rate": passed / total_questions if total_questions else 0,
        "generation_time": gen_time,
        "evaluation_time": eval_time,
        "by_type": by_type,
        "by_course": by_course,
    }

    db[RUNS_COL].insert_one(run_doc)

    # Summary (gen failures count as 0s)
    print(f"\n{'─'*50}")
    print(f"RESULTS: {passed}/{total_questions} passed ({100*passed/total_questions:.1f}%)")
    if gen_errors:
        print(f"  (includes {gen_errors} generation failures as 0s)")
    print(f"{'─'*50}")
    for qtype in QUESTION_TYPES:
        s = by_type[qtype]
        print(f"  {qtype:10} {s['passed']:3}/{s['total']:3} ({100*s['rate']:5.1f}%)")
    print(f"\nSaved to MongoDB: {run_id}")

    return run_id


if __name__ == "__main__":
    asyncio.run(run_benchmark())
