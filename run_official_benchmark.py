#!/usr/bin/env python3
"""
Official AP Question Types Benchmark

Tests all official AP question types against randomly sampled standards:
- MCQ (single)
- MCQ Set (stimulus + 3-4 questions)
- SAQ (3 parts)
- LEQ (long essay)
- DBQ (7 documents)

Samples at least 50 standards from across the curriculum.
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

# MongoDB connection
MONGODB_URI = os.environ.get('MONGODB_URI')
if not MONGODB_URI:
    raise ValueError("MONGODB_URI environment variable is required")

from pymongo import MongoClient

# Configuration
ENDPOINT_URL = "http://192.168.1.24:8000/generate"
NUM_STANDARDS = 50  # Minimum standards to sample
QUESTION_TYPES = ["mcq", "mcq_set", "saq", "leq", "dbq"]
DIFFICULTIES = ["easy", "medium", "hard"]
REQUEST_TIMEOUT = 180  # 3 minutes for DBQ
MAX_CONCURRENT = 5


@dataclass
class BenchmarkResult:
    task_id: str
    question_type: str
    difficulty: str
    node_id: str
    course: str
    unit: int
    cluster: str
    success: bool
    generation_time: float
    error: Optional[str] = None
    response: Optional[Dict] = None


@dataclass
class BenchmarkStats:
    total: int = 0
    success: int = 0
    failed: int = 0
    by_type: Dict[str, Dict[str, int]] = field(default_factory=dict)
    by_course: Dict[str, Dict[str, int]] = field(default_factory=dict)
    by_unit: Dict[str, Dict[str, int]] = field(default_factory=dict)
    errors: List[str] = field(default_factory=list)
    generation_times: Dict[str, List[float]] = field(default_factory=dict)


def get_random_standards(num_standards: int = 50) -> List[Dict[str, Any]]:
    """Sample random standards from MongoDB across both courses."""
    client = MongoClient(MONGODB_URI, serverSelectionTimeoutMS=10000)
    db = client['ap_social_studies']

    # Get standards from both courses
    apush_count = int(num_standards * 0.6)  # 60% APUSH
    apwh_count = num_standards - apush_count  # 40% APWH

    # Sample from APUSH
    apush_facts = list(db.facts.aggregate([
        {"$match": {"course": "APUSH"}},
        {"$sample": {"size": apush_count}}
    ]))

    # Sample from APWH
    apwh_facts = list(db.facts.aggregate([
        {"$match": {"course": "APWH"}},
        {"$sample": {"size": apwh_count}}
    ]))

    all_facts = apush_facts + apwh_facts
    random.shuffle(all_facts)
    return all_facts


def build_payload(fact: Dict, question_type: str, difficulty: str) -> Dict:
    """Build generation request payload."""
    node_id = fact.get('node_id', str(uuid.uuid4())[:8])

    # Helper to safely convert values to strings (handles datetime)
    def safe_str(val):
        if val is None:
            return ''
        if hasattr(val, 'isoformat'):  # datetime
            return val.isoformat()
        return str(val)

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

    # Add type-specific fields
    if question_type == "leq":
        # Randomly assign reasoning type (use 'ccot' not 'continuity_and_change')
        payload["reasoning_type"] = random.choice(["causation", "comparison", "ccot"])

    return payload


async def generate_question(
    client: httpx.AsyncClient,
    payload: Dict,
    stats: BenchmarkStats
) -> BenchmarkResult:
    """Generate a single question and track result."""
    task_id = str(uuid.uuid4())[:8]
    question_type = payload["type"]
    difficulty = payload["difficulty"]
    node_id = payload.get("node_id", "unknown")
    course = payload.get("course", "APUSH")
    unit = payload.get("unit", 0)
    cluster = payload.get("topic", "")

    start_time = time.time()

    try:
        response = await client.post(
            ENDPOINT_URL,
            json=payload,
            timeout=REQUEST_TIMEOUT
        )

        generation_time = time.time() - start_time

        if response.status_code == 200:
            data = response.json()

            # Track success
            stats.total += 1
            stats.success += 1

            # Track by type
            if question_type not in stats.by_type:
                stats.by_type[question_type] = {"success": 0, "failed": 0}
            stats.by_type[question_type]["success"] += 1

            # Track by course
            if course not in stats.by_course:
                stats.by_course[course] = {"success": 0, "failed": 0}
            stats.by_course[course]["success"] += 1

            # Track generation time
            if question_type not in stats.generation_times:
                stats.generation_times[question_type] = []
            stats.generation_times[question_type].append(generation_time)

            return BenchmarkResult(
                task_id=task_id,
                question_type=question_type,
                difficulty=difficulty,
                node_id=node_id,
                course=course,
                unit=unit,
                cluster=cluster,
                success=True,
                generation_time=generation_time,
                response=data
            )
        else:
            error_msg = f"HTTP {response.status_code}: {response.text[:200]}"
            stats.total += 1
            stats.failed += 1

            if question_type not in stats.by_type:
                stats.by_type[question_type] = {"success": 0, "failed": 0}
            stats.by_type[question_type]["failed"] += 1

            if course not in stats.by_course:
                stats.by_course[course] = {"success": 0, "failed": 0}
            stats.by_course[course]["failed"] += 1

            stats.errors.append(f"{question_type}/{difficulty}: {error_msg}")

            return BenchmarkResult(
                task_id=task_id,
                question_type=question_type,
                difficulty=difficulty,
                node_id=node_id,
                course=course,
                unit=unit,
                cluster=cluster,
                success=False,
                generation_time=time.time() - start_time,
                error=error_msg
            )

    except Exception as e:
        error_msg = str(e)
        stats.total += 1
        stats.failed += 1

        if question_type not in stats.by_type:
            stats.by_type[question_type] = {"success": 0, "failed": 0}
        stats.by_type[question_type]["failed"] += 1

        if course not in stats.by_course:
            stats.by_course[course] = {"success": 0, "failed": 0}
        stats.by_course[course]["failed"] += 1

        stats.errors.append(f"{question_type}/{difficulty}: {error_msg}")

        return BenchmarkResult(
            task_id=task_id,
            question_type=question_type,
            difficulty=difficulty,
            node_id=node_id,
            course=course,
            unit=unit,
            cluster=cluster,
            success=False,
            generation_time=time.time() - start_time,
            error=error_msg
        )


async def run_benchmark():
    """Run the full benchmark."""
    run_id = str(uuid.uuid4())[:8]
    print(f"\nAP Benchmark | {run_id} | {NUM_STANDARDS} standards")

    standards = get_random_standards(NUM_STANDARDS)

    type_assignments = []
    for i, standard in enumerate(standards):
        qtype = QUESTION_TYPES[i % len(QUESTION_TYPES)]
        difficulty = random.choice(DIFFICULTIES)
        type_assignments.append((standard, qtype, difficulty))
    random.shuffle(type_assignments)

    # Run tasks with concurrency limit
    stats = BenchmarkStats()
    results = []
    semaphore = asyncio.Semaphore(MAX_CONCURRENT)

    async def bounded_generate(client, payload):
        async with semaphore:
            return await generate_question(client, payload, stats)

    start_time = time.time()

    async with httpx.AsyncClient() as client:
        # Create all tasks
        generation_tasks = []
        for standard, qtype, difficulty in type_assignments:
            payload = build_payload(standard, qtype, difficulty)
            generation_tasks.append(bounded_generate(client, payload))

        # Progress tracking
        completed = 0
        total = len(generation_tasks)

        for coro in asyncio.as_completed(generation_tasks):
            result = await coro
            results.append(result)
            completed += 1

            print(f"\rGenerating: {completed}/{total}", end="", flush=True)

    total_time = time.time() - start_time
    print(f"\rGenerated: {stats.success}/{stats.total} in {total_time:.0f}s" + " " * 20)

    print(f"\n{'─'*50}")
    print(f"RESULTS: {stats.success}/{stats.total} ({100*stats.success/stats.total:.1f}%)")
    print(f"{'─'*50}")
    for qtype in QUESTION_TYPES:
        if qtype in stats.by_type:
            s = stats.by_type[qtype]["success"]
            t = s + stats.by_type[qtype]["failed"]
            print(f"  {qtype:10} {s:3}/{t:3} ({100*s/t if t else 0:5.1f}%)")

    # Save results
    results_file = f"benchmark_official_{run_id}.json"
    with open(results_file, 'w') as f:
        json.dump({
            "run_id": run_id,
            "timestamp": datetime.now().isoformat(),
            "endpoint": ENDPOINT_URL,
            "total_standards": len(standards),
            "total_tasks": len(type_assignments),
            "success": stats.success,
            "failed": stats.failed,
            "success_rate": stats.success / stats.total if stats.total > 0 else 0,
            "total_time_seconds": total_time,
            "by_type": stats.by_type,
            "by_course": stats.by_course,
            "generation_times": {k: {"avg": sum(v)/len(v), "min": min(v), "max": max(v)}
                                for k, v in stats.generation_times.items()},
            "errors": stats.errors,
            "results": [
                {
                    "task_id": r.task_id,
                    "type": r.question_type,
                    "difficulty": r.difficulty,
                    "course": r.course,
                    "unit": r.unit,
                    "node_id": r.node_id,
                    "success": r.success,
                    "time": r.generation_time,
                    "error": r.error
                }
                for r in results
            ]
        }, f, indent=2)

    print(f"\nSaved: {results_file}")
    return stats


if __name__ == "__main__":
    asyncio.run(run_benchmark())
