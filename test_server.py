#!/usr/bin/env python3
"""
Test suite for the AP Question Evaluation Server.

Tests:
1. Concurrent request handling
2. Evaluation consistency with database results
3. All question types
"""

import asyncio
import json
import os
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime

import httpx
import requests
from pymongo import MongoClient
from dotenv import load_dotenv

load_dotenv()

# Configuration
SERVER_URL = "http://localhost:8080"
MONGODB_URI = os.environ.get('MONGODB_URI')
DB_NAME = "ap_social_studies"


def get_db():
    client = MongoClient(MONGODB_URI, serverSelectionTimeoutMS=10000)
    return client[DB_NAME]


# ============================================
# Test 1: Concurrent Requests
# ============================================

def test_concurrent_get_standards(num_requests: int = 20):
    """Test concurrent GET /get_standard requests."""
    print(f"\n{'='*60}")
    print(f"TEST 1: Concurrent GET /get_standard ({num_requests} requests)")
    print('='*60)

    def make_request(i):
        start = time.time()
        try:
            resp = requests.get(f"{SERVER_URL}/get_standard", timeout=10)
            elapsed = time.time() - start
            return {
                "index": i,
                "success": resp.status_code == 200,
                "status_code": resp.status_code,
                "elapsed": elapsed,
                "data": resp.json() if resp.status_code == 200 else None
            }
        except Exception as e:
            return {
                "index": i,
                "success": False,
                "error": str(e),
                "elapsed": time.time() - start
            }

    start_time = time.time()

    with ThreadPoolExecutor(max_workers=10) as executor:
        results = list(executor.map(make_request, range(num_requests)))

    total_time = time.time() - start_time

    # Analyze results
    successes = sum(1 for r in results if r["success"])
    failures = num_requests - successes
    avg_time = sum(r["elapsed"] for r in results) / num_requests
    max_time = max(r["elapsed"] for r in results)
    min_time = min(r["elapsed"] for r in results)

    print(f"\nResults:")
    print(f"  Total requests:    {num_requests}")
    print(f"  Successful:        {successes}")
    print(f"  Failed:            {failures}")
    print(f"  Total time:        {total_time:.2f}s")
    print(f"  Avg response time: {avg_time*1000:.0f}ms")
    print(f"  Min response time: {min_time*1000:.0f}ms")
    print(f"  Max response time: {max_time*1000:.0f}ms")
    print(f"  Throughput:        {num_requests/total_time:.1f} req/s")

    if failures > 0:
        print(f"\n  ❌ FAILED - {failures} requests failed")
        for r in results:
            if not r["success"]:
                print(f"    Request {r['index']}: {r.get('error', r.get('status_code'))}")
    else:
        print(f"\n  ✅ PASSED - All requests successful")

    return successes == num_requests


# ============================================
# Test 2: Evaluation Consistency
# ============================================

def test_evaluation_consistency():
    """Test that server evaluations match database results."""
    print(f"\n{'='*60}")
    print("TEST 2: Evaluation Consistency with Database")
    print('='*60)

    db = get_db()

    # Get recent passing questions from database
    passing_evals = list(db.benchmark_evaluations.find({
        "passed": True,
        "overall_score": {"$gte": 0.9}  # High-scoring questions
    }).sort("created_at", -1).limit(5))

    if not passing_evals:
        print("  No passing evaluations found in database")
        return False

    print(f"\nTesting {len(passing_evals)} high-scoring questions from database...")

    results = []
    for i, eval_doc in enumerate(passing_evals):
        qid = eval_doc["question_id"]
        question = db.benchmark_questions.find_one({"_id": qid})

        if not question:
            print(f"  Question {qid} not found")
            continue

        qtype = eval_doc["type"]
        db_score = eval_doc["overall_score"]
        db_passed = eval_doc["passed"]

        # Build request for server
        question_data = question.get("question_data", {})
        output = question_data.get("output", question_data)

        request_body = {
            "type": qtype,
            "difficulty": question.get("difficulty", "medium"),
            "request": {
                "node_id": question.get("node_id", ""),
                "course": question.get("course", "APUSH"),
                "unit": question.get("unit", 1),
                "topic": question.get("topic", ""),
                "learning_objective": question.get("learning_objective", ""),
                "curriculum_fact": question_data.get("request", {}).get("curriculum_fact", ""),
                "time_period": question_data.get("request", {}).get("time_period", ""),
                "theme": question_data.get("request", {}).get("theme", ""),
            },
            "output": output
        }

        # Call server
        try:
            resp = requests.post(
                f"{SERVER_URL}/evaluate",
                json=request_body,
                timeout=120
            )

            if resp.status_code != 200:
                print(f"  ❌ {qtype.upper()} #{i+1}: Server error {resp.status_code}")
                print(f"     {resp.json().get('error', 'Unknown error')[:100]}")
                results.append({"match": False, "error": True})
                continue

            server_result = resp.json()
            server_score = server_result.get("overall_score", 0)
            server_passed = server_result.get("passed", False)

            # Compare results
            score_diff = abs(server_score - db_score)
            pass_match = server_passed == db_passed

            status = "✅" if score_diff < 0.15 and pass_match else "⚠️"

            print(f"  {status} {qtype.upper()} #{i+1}:")
            print(f"     DB Score: {db_score:.3f} | Server Score: {server_score:.3f} | Diff: {score_diff:.3f}")
            print(f"     DB Passed: {db_passed} | Server Passed: {server_passed}")

            results.append({
                "match": score_diff < 0.15 and pass_match,
                "score_diff": score_diff,
                "pass_match": pass_match
            })

        except Exception as e:
            print(f"  ❌ {qtype.upper()} #{i+1}: Exception - {str(e)[:100]}")
            results.append({"match": False, "error": True})

    # Summary
    matches = sum(1 for r in results if r.get("match"))
    total = len(results)

    print(f"\nSummary:")
    print(f"  Consistent: {matches}/{total}")

    if matches == total:
        print(f"\n  ✅ PASSED - All evaluations consistent")
    else:
        print(f"\n  ⚠️ WARNING - Some evaluations differ (may be due to LLM variance)")

    return matches >= total * 0.8  # Allow 20% variance due to LLM


# ============================================
# Test 3: All Question Types
# ============================================

def test_all_question_types():
    """Test evaluation of all question types with real data."""
    print(f"\n{'='*60}")
    print("TEST 3: All Question Types")
    print('='*60)

    db = get_db()

    question_types = ["mcq", "mcq_set", "saq", "leq", "dbq"]
    results = {}

    for qtype in question_types:
        # Get a passing question of this type
        eval_doc = db.benchmark_evaluations.find_one({
            "type": qtype,
            "passed": True,
            "overall_score": {"$gte": 0.85}
        }, sort=[("created_at", -1)])

        if not eval_doc:
            print(f"\n  ⚠️ {qtype.upper()}: No passing question found in DB")
            results[qtype] = {"status": "skip", "reason": "no data"}
            continue

        qid = eval_doc["question_id"]
        question = db.benchmark_questions.find_one({"_id": qid})

        if not question:
            print(f"\n  ⚠️ {qtype.upper()}: Question document not found")
            results[qtype] = {"status": "skip", "reason": "missing question"}
            continue

        question_data = question.get("question_data", {})
        output = question_data.get("output", question_data)
        request_context = question_data.get("request", {})

        # Build request
        request_body = {
            "type": qtype,
            "difficulty": question.get("difficulty", "medium"),
            "request": {
                "node_id": request_context.get("node_id", question.get("node_id", "")),
                "course": request_context.get("course", question.get("course", "APUSH")),
                "unit": request_context.get("unit", question.get("unit", 1)),
                "topic": request_context.get("topic", question.get("topic", "")),
                "learning_objective": request_context.get("learning_objective", question.get("learning_objective", "")),
                "curriculum_fact": request_context.get("curriculum_fact", ""),
                "time_period": request_context.get("time_period", ""),
                "theme": request_context.get("theme", ""),
            },
            "output": output
        }

        print(f"\n  Testing {qtype.upper()}...")
        print(f"    Topic: {request_body['request']['topic'][:50]}...")
        print(f"    DB Score: {eval_doc['overall_score']:.3f}")

        try:
            start = time.time()
            resp = requests.post(
                f"{SERVER_URL}/evaluate",
                json=request_body,
                timeout=180
            )
            elapsed = time.time() - start

            if resp.status_code != 200:
                error = resp.json().get("error", "Unknown")
                print(f"    ❌ Server error: {error[:100]}")
                results[qtype] = {"status": "error", "error": error}
                continue

            server_result = resp.json()
            server_score = server_result.get("overall_score", 0)
            server_passed = server_result.get("passed", False)

            print(f"    Server Score: {server_score:.3f}")
            print(f"    Server Passed: {server_passed}")
            print(f"    Response Time: {elapsed:.1f}s")

            if server_result.get("issues"):
                print(f"    Issues: {len(server_result['issues'])}")
                for issue in server_result["issues"][:2]:
                    if isinstance(issue, dict):
                        sev = issue.get('severity', 'unknown')
                        dim = issue.get('dimension', 'unknown')
                        exp = issue.get('explanation', str(issue))[:60]
                        print(f"      - [{sev}] {dim}: {exp}...")
                    else:
                        print(f"      - {str(issue)[:80]}...")

            results[qtype] = {
                "status": "success",
                "db_score": eval_doc["overall_score"],
                "server_score": server_score,
                "server_passed": server_passed,
                "elapsed": elapsed
            }

        except Exception as e:
            print(f"    ❌ Exception: {str(e)[:100]}")
            results[qtype] = {"status": "error", "error": str(e)}

    # Summary
    print(f"\n{'─'*60}")
    print("Summary:")
    print(f"{'─'*60}")

    successes = 0
    for qtype in question_types:
        r = results.get(qtype, {})
        if r.get("status") == "success":
            successes += 1
            emoji = "✅"
        elif r.get("status") == "skip":
            emoji = "⚠️"
        else:
            emoji = "❌"

        if r.get("status") == "success":
            print(f"  {emoji} {qtype.upper():10} | DB: {r['db_score']:.2f} | Server: {r['server_score']:.2f} | {r['elapsed']:.1f}s")
        else:
            print(f"  {emoji} {qtype.upper():10} | {r.get('status', 'unknown')}: {r.get('reason', r.get('error', ''))[:40]}")

    if successes == len(question_types):
        print(f"\n  ✅ PASSED - All question types evaluated successfully")
    else:
        print(f"\n  ⚠️ {successes}/{len(question_types)} types evaluated successfully")

    return successes >= 4  # At least 4 of 5 types should work


# ============================================
# Test 4: Concurrent Evaluations
# ============================================

async def test_concurrent_evaluations(num_requests: int = 5):
    """Test concurrent POST /evaluate requests."""
    print(f"\n{'='*60}")
    print(f"TEST 4: Concurrent Evaluations ({num_requests} requests)")
    print('='*60)

    db = get_db()

    # Get several passing questions
    passing_evals = list(db.benchmark_evaluations.find({
        "passed": True,
        "type": "mcq"  # MCQ is fastest to evaluate
    }).sort("created_at", -1).limit(num_requests))

    if len(passing_evals) < num_requests:
        print(f"  Only {len(passing_evals)} questions available")
        num_requests = len(passing_evals)

    # Build requests
    requests_to_make = []
    for eval_doc in passing_evals:
        qid = eval_doc["question_id"]
        question = db.benchmark_questions.find_one({"_id": qid})
        if not question:
            continue

        question_data = question.get("question_data", {})
        output = question_data.get("output", question_data)
        request_context = question_data.get("request", {})

        request_body = {
            "type": eval_doc["type"],
            "difficulty": question.get("difficulty", "medium"),
            "request": {
                "node_id": request_context.get("node_id", ""),
                "course": request_context.get("course", "APUSH"),
                "unit": request_context.get("unit", 1),
                "topic": request_context.get("topic", ""),
                "learning_objective": request_context.get("learning_objective", ""),
                "curriculum_fact": request_context.get("curriculum_fact", ""),
                "time_period": request_context.get("time_period", ""),
                "theme": request_context.get("theme", ""),
            },
            "output": output
        }
        requests_to_make.append(request_body)

    print(f"\nSending {len(requests_to_make)} concurrent evaluation requests...")

    async def make_eval_request(client, req_body, index):
        start = time.time()
        try:
            resp = await client.post(
                f"{SERVER_URL}/evaluate",
                json=req_body,
                timeout=180
            )
            elapsed = time.time() - start
            data = resp.json()
            return {
                "index": index,
                "success": resp.status_code == 200 and data.get("success"),
                "passed": data.get("passed"),
                "score": data.get("overall_score"),
                "elapsed": elapsed
            }
        except Exception as e:
            return {
                "index": index,
                "success": False,
                "error": str(e),
                "elapsed": time.time() - start
            }

    start_time = time.time()

    async with httpx.AsyncClient() as client:
        tasks = [make_eval_request(client, req, i) for i, req in enumerate(requests_to_make)]
        results = await asyncio.gather(*tasks)

    total_time = time.time() - start_time

    # Analyze
    successes = sum(1 for r in results if r["success"])
    failures = len(results) - successes
    avg_time = sum(r["elapsed"] for r in results) / len(results)

    print(f"\nResults:")
    print(f"  Total requests:    {len(results)}")
    print(f"  Successful:        {successes}")
    print(f"  Failed:            {failures}")
    print(f"  Total time:        {total_time:.1f}s")
    print(f"  Avg response time: {avg_time:.1f}s")

    for r in results:
        if r["success"]:
            status = "✅" if r.get("passed") else "❌"
            print(f"    {status} Request {r['index']}: score={r.get('score', 0):.2f}, time={r['elapsed']:.1f}s")
        else:
            print(f"    ❌ Request {r['index']}: {r.get('error', 'failed')[:50]}")

    if successes == len(results):
        print(f"\n  ✅ PASSED - All concurrent evaluations completed")
    else:
        print(f"\n  ⚠️ {successes}/{len(results)} evaluations completed")

    return successes == len(results)


# ============================================
# Main
# ============================================

def main():
    print("\n" + "="*60)
    print("AP Question Evaluation Server - Test Suite")
    print("="*60)
    print(f"Server URL: {SERVER_URL}")
    print(f"Time: {datetime.now().isoformat()}")

    # Check server health
    try:
        resp = requests.get(f"{SERVER_URL}/health", timeout=5)
        if resp.status_code != 200:
            print(f"\n❌ Server not healthy: {resp.status_code}")
            return
        print(f"Server Status: {resp.json()['status']}")
    except Exception as e:
        print(f"\n❌ Cannot connect to server: {e}")
        return

    results = {}

    # Test 1: Concurrent GET requests
    results["concurrent_get"] = test_concurrent_get_standards(20)

    # Test 2: Evaluation consistency
    results["consistency"] = test_evaluation_consistency()

    # Test 3: All question types
    results["all_types"] = test_all_question_types()

    # Test 4: Concurrent evaluations
    results["concurrent_eval"] = asyncio.run(test_concurrent_evaluations(3))

    # Final Summary
    print("\n" + "="*60)
    print("FINAL RESULTS")
    print("="*60)

    all_passed = True
    for test_name, passed in results.items():
        status = "✅ PASSED" if passed else "❌ FAILED"
        print(f"  {test_name}: {status}")
        if not passed:
            all_passed = False

    if all_passed:
        print(f"\n{'='*60}")
        print("🎉 ALL TESTS PASSED")
        print("="*60)
    else:
        print(f"\n{'='*60}")
        print("⚠️ SOME TESTS FAILED")
        print("="*60)


if __name__ == "__main__":
    main()
