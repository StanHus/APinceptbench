"""
Benchmark Orchestrator - End-to-End Evaluation Pipeline

Orchestrates the full benchmark workflow:
1. Generate test requests from curriculum facts
2. Send requests to generation endpoint in parallel
3. Store request+response pairs in MongoDB
4. Evaluate responses using the evaluator
5. Store evaluation results in MongoDB

All data is persisted to MongoDB with full traceability.

Usage:
    from ap_benchmark.core.orchestrator import BenchmarkOrchestrator

    orchestrator = BenchmarkOrchestrator(
        endpoint_url="http://192.168.1.10:8000/generate",
        concurrency=5,
    )
    run_id = await orchestrator.run_benchmark(
        course="APUSH",
        units=[1, 2, 3],
        questions_per_unit=10,
    )
"""

import asyncio
import logging
import time
import traceback
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional, Callable

import httpx
from pymongo import WriteConcern
from pymongo.errors import PyMongoError

from .database import get_database
from .evaluator import evaluate_question
from .models import BenchmarkResult, EvaluationRequest

logger = logging.getLogger(__name__)

# MongoDB collection names
RUNS_COLLECTION = "benchmark_runs"
REQUESTS_COLLECTION = "benchmark_requests"
RESULTS_COLLECTION = "benchmark_results"

# Write concern for important operations
WRITE_CONCERN = WriteConcern(w=1, j=True)  # Acknowledge write, journal


@dataclass
class GenerationRequest:
    """A request to send to the generation endpoint."""
    request_id: str
    payload: Dict[str, Any]
    node_id: Optional[str] = None
    curriculum_fact: Optional[Dict[str, Any]] = None  # Full fact from MongoDB
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class GenerationResponse:
    """Response from the generation endpoint."""
    request_id: str
    request_payload: Dict[str, Any]
    response_data: Optional[Dict[str, Any]] = None
    raw_response_text: Optional[str] = None  # Raw response for debugging
    http_status_code: Optional[int] = None
    error: Optional[str] = None
    error_traceback: Optional[str] = None
    latency_ms: float = 0.0
    attempt_count: int = 1
    timestamp: datetime = field(default_factory=datetime.utcnow)


@dataclass
class BenchmarkRun:
    """A complete benchmark run."""
    run_id: str
    endpoint_url: str
    course: str
    started_at: datetime
    completed_at: Optional[datetime] = None
    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    evaluated_count: int = 0
    evaluation_errors: int = 0
    pass_count: int = 0
    fail_count: int = 0
    average_score: float = 0.0
    average_latency_ms: float = 0.0
    status: str = "running"  # running, completed, failed
    error_message: Optional[str] = None
    config: Dict[str, Any] = field(default_factory=dict)


class BenchmarkOrchestrator:
    """
    Orchestrates benchmark runs against a generation endpoint.

    Handles parallel request generation, response collection,
    evaluation, and result storage in MongoDB.

    All operations are persisted with write acknowledgment.
    """

    def __init__(
        self,
        endpoint_url: str,
        concurrency: int = 5,
        timeout: float = 30.0,
        retry_attempts: int = 2,
        db_retry_attempts: int = 3,
    ):
        """
        Initialize the orchestrator.

        Args:
            endpoint_url: URL of the generation endpoint
            concurrency: Max concurrent requests
            timeout: Request timeout in seconds
            retry_attempts: Number of retry attempts for failed HTTP requests
            db_retry_attempts: Number of retry attempts for failed DB writes
        """
        self.endpoint_url = endpoint_url
        self.concurrency = concurrency
        self.timeout = timeout
        self.retry_attempts = retry_attempts
        self.db_retry_attempts = db_retry_attempts
        self._semaphore: Optional[asyncio.Semaphore] = None

    def _get_db(self):
        """Get MongoDB database, raising if unavailable."""
        db = get_database()
        if db is None:
            raise RuntimeError("MongoDB connection required for orchestrator. Set MONGODB_URI.")
        return db

    def _ensure_indexes(self):
        """Ensure MongoDB indexes exist for efficient queries."""
        db = self._get_db()

        # Runs collection indexes
        runs = db[RUNS_COLLECTION]
        runs.create_index("run_id", unique=True)
        runs.create_index("started_at")
        runs.create_index("status")
        runs.create_index("course")
        runs.create_index([("course", 1), ("started_at", -1)])

        # Requests collection indexes
        requests = db[REQUESTS_COLLECTION]
        requests.create_index("run_id")
        requests.create_index("request_id", unique=True)
        requests.create_index("node_id")
        requests.create_index([("run_id", 1), ("status", 1)])
        requests.create_index([("run_id", 1), ("evaluated", 1)])

        # Results collection indexes
        results = db[RESULTS_COLLECTION]
        results.create_index("run_id")
        results.create_index("request_id", unique=True)
        results.create_index("node_id")
        results.create_index([("run_id", 1), ("passed", 1)])
        results.create_index([("run_id", 1), ("overall_score", 1)])
        results.create_index("evaluated_at")

        logger.info("MongoDB indexes ensured")

    def _db_write_with_retry(
        self,
        operation: Callable,
        operation_name: str,
    ) -> Any:
        """Execute a database write operation with retry logic."""
        last_error = None
        for attempt in range(self.db_retry_attempts):
            try:
                result = operation()
                return result
            except PyMongoError as e:
                last_error = e
                logger.warning(f"DB write failed ({operation_name}), attempt {attempt + 1}: {e}")
                if attempt < self.db_retry_attempts - 1:
                    time.sleep(0.5 * (attempt + 1))

        logger.error(f"DB write failed after {self.db_retry_attempts} attempts ({operation_name}): {last_error}")
        raise last_error

    async def _send_request(
        self,
        client: httpx.AsyncClient,
        request: GenerationRequest,
    ) -> GenerationResponse:
        """Send a single request to the generation endpoint."""
        start_time = time.perf_counter()
        attempt_count = 0

        for attempt in range(self.retry_attempts + 1):
            attempt_count = attempt + 1
            try:
                async with self._semaphore:
                    response = await client.post(
                        self.endpoint_url,
                        json=request.payload,
                        timeout=self.timeout,
                    )

                    latency_ms = (time.perf_counter() - start_time) * 1000
                    raw_text = response.text

                    response.raise_for_status()

                    return GenerationResponse(
                        request_id=request.request_id,
                        request_payload=request.payload,
                        response_data=response.json(),
                        raw_response_text=raw_text[:10000],  # Limit stored size
                        http_status_code=response.status_code,
                        latency_ms=latency_ms,
                        attempt_count=attempt_count,
                    )

            except httpx.HTTPStatusError as e:
                if attempt == self.retry_attempts:
                    return GenerationResponse(
                        request_id=request.request_id,
                        request_payload=request.payload,
                        raw_response_text=e.response.text[:2000] if e.response else None,
                        http_status_code=e.response.status_code if e.response else None,
                        error=f"HTTP {e.response.status_code}: {e.response.text[:500]}",
                        error_traceback=traceback.format_exc(),
                        latency_ms=(time.perf_counter() - start_time) * 1000,
                        attempt_count=attempt_count,
                    )
                await asyncio.sleep(1 * (attempt + 1))

            except Exception as e:
                if attempt == self.retry_attempts:
                    return GenerationResponse(
                        request_id=request.request_id,
                        request_payload=request.payload,
                        error=f"{type(e).__name__}: {str(e)}",
                        error_traceback=traceback.format_exc(),
                        latency_ms=(time.perf_counter() - start_time) * 1000,
                        attempt_count=attempt_count,
                    )
                await asyncio.sleep(1 * (attempt + 1))

        return GenerationResponse(
            request_id=request.request_id,
            request_payload=request.payload,
            error="Max retries exceeded",
            attempt_count=attempt_count,
        )

    async def _send_requests_parallel(
        self,
        requests: List[GenerationRequest],
        progress_callback: Optional[Callable[[int, int], None]] = None,
    ) -> List[GenerationResponse]:
        """Send multiple requests in parallel with concurrency limit."""
        self._semaphore = asyncio.Semaphore(self.concurrency)

        async with httpx.AsyncClient() as client:
            tasks = [self._send_request(client, req) for req in requests]

            responses = []
            for i, coro in enumerate(asyncio.as_completed(tasks)):
                response = await coro
                responses.append(response)
                if progress_callback:
                    progress_callback(i + 1, len(requests))

            return responses

    def _generate_requests_from_facts(
        self,
        course: str,
        units: Optional[List[int]] = None,
        question_types: Optional[List[str]] = None,
        questions_per_unit: int = 10,
        sample_from_db: bool = True,
    ) -> List[GenerationRequest]:
        """
        Generate benchmark requests from curriculum facts.

        Args:
            course: Course code (APUSH, APWH)
            units: Specific units to test (None = all)
            question_types: Types to generate (None = ["mcq"])
            questions_per_unit: How many questions per unit
            sample_from_db: If True, sample facts from MongoDB

        Returns:
            List of GenerationRequest objects
        """
        if question_types is None:
            question_types = ["mcq"]

        requests = []

        if sample_from_db:
            from .curriculum_db import get_facts_by_course_unit

            if units is None:
                units = list(range(1, 10))

            for unit in units:
                facts = get_facts_by_course_unit(course, unit)
                if not facts:
                    logger.warning(f"No facts found for {course} unit {unit}")
                    continue

                import random
                sampled = random.sample(facts, min(len(facts), questions_per_unit))

                for fact in sampled:
                    for qtype in question_types:
                        request_id = str(uuid.uuid4())
                        requests.append(GenerationRequest(
                            request_id=request_id,
                            payload={
                                "type": qtype,
                                "topic": fact.get("cluster", ""),
                                "course": course,
                                "unit": unit,
                                "node_id": fact.get("node_id"),
                                "learning_objective": fact.get("learning_objective", ""),
                                "statement": fact.get("statement", ""),
                                "difficulty": "medium",
                            },
                            node_id=fact.get("node_id"),
                            curriculum_fact=fact,  # Store full fact
                            metadata={
                                "unit": unit,
                                "theme": fact.get("theme"),
                                "classification": fact.get("classification"),
                                "date": fact.get("date"),
                            }
                        ))
        else:
            if units is None:
                units = list(range(1, 10))

            from .curriculum import AP_COURSE_UNITS
            course_units = AP_COURSE_UNITS.get(course, {})

            for unit in units:
                unit_topic = course_units.get(unit, f"Unit {unit}")
                for _ in range(questions_per_unit):
                    for qtype in question_types:
                        request_id = str(uuid.uuid4())
                        requests.append(GenerationRequest(
                            request_id=request_id,
                            payload={
                                "type": qtype,
                                "topic": unit_topic,
                                "course": course,
                                "unit": unit,
                                "difficulty": "medium",
                            },
                            metadata={"unit": unit}
                        ))

        return requests

    def _store_request_response(
        self,
        run_id: str,
        request: GenerationRequest,
        response: GenerationResponse,
    ) -> str:
        """
        Store a request+response pair in MongoDB.

        Returns the inserted document ID.
        """
        db = self._get_db()
        collection = db[REQUESTS_COLLECTION].with_options(write_concern=WRITE_CONCERN)

        doc = {
            "run_id": run_id,
            "request_id": request.request_id,

            # Request data
            "request_payload": request.payload,
            "node_id": request.node_id,
            "curriculum_fact": request.curriculum_fact,
            "request_metadata": request.metadata,

            # Response data
            "response_data": response.response_data,
            "raw_response_text": response.raw_response_text,
            "http_status_code": response.http_status_code,

            # Error tracking
            "error": response.error,
            "error_traceback": response.error_traceback,

            # Metrics
            "latency_ms": response.latency_ms,
            "attempt_count": response.attempt_count,
            "timestamp": response.timestamp,

            # Status tracking
            "status": "success" if response.response_data else "error",
            "evaluated": False,
            "evaluation_id": None,

            # Timestamps
            "created_at": datetime.utcnow(),
        }

        def do_insert():
            result = collection.insert_one(doc)
            if not result.acknowledged:
                raise PyMongoError("Write not acknowledged")
            return str(result.inserted_id)

        return self._db_write_with_retry(do_insert, f"store_request:{request.request_id}")

    def _store_evaluation_result(
        self,
        run_id: str,
        request_id: str,
        node_id: Optional[str],
        request_payload: Dict[str, Any],
        response_data: Dict[str, Any],
        curriculum_fact: Optional[Dict[str, Any]],
        result: BenchmarkResult,
    ) -> str:
        """
        Store evaluation result in MongoDB.

        Returns the inserted document ID.
        """
        db = self._get_db()
        collection = db[RESULTS_COLLECTION].with_options(write_concern=WRITE_CONCERN)

        doc = {
            "run_id": run_id,
            "request_id": request_id,
            "node_id": node_id,

            # Full context for reproducibility
            "request_payload": request_payload,
            "response_data": response_data,
            "curriculum_fact": curriculum_fact,

            # Evaluation results
            "passed": result.passed,
            "overall_score": result.overall_score,
            "question_hash": result.question_hash,
            "prompt_version": result.prompt_version,
            "question_type": result.question_type.value,

            # Failure counts
            "critical_failures": result.critical_failures,
            "non_critical_failures": result.non_critical_failures,

            # All dimension scores with full detail
            "dimensions": {
                "factual_accuracy": {
                    "score": result.factual_accuracy.score,
                    "reasoning": result.factual_accuracy.reasoning,
                    "issues": result.factual_accuracy.issues,
                },
                "curriculum_alignment": {
                    "score": result.curriculum_alignment.score,
                    "reasoning": result.curriculum_alignment.reasoning,
                    "issues": result.curriculum_alignment.issues,
                },
                "cognitive_demand": {
                    "score": result.cognitive_demand.score,
                    "reasoning": result.cognitive_demand.reasoning,
                    "issues": result.cognitive_demand.issues,
                },
                "distractor_quality": {
                    "score": result.distractor_quality.score,
                    "reasoning": result.distractor_quality.reasoning,
                    "issues": result.distractor_quality.issues,
                },
                "explanation_quality": {
                    "score": result.explanation_quality.score,
                    "reasoning": result.explanation_quality.reasoning,
                    "issues": result.explanation_quality.issues,
                },
                "clarity": {
                    "score": result.clarity.score,
                    "reasoning": result.clarity.reasoning,
                    "issues": result.clarity.issues,
                },
                "difficulty_alignment": {
                    "score": result.difficulty_alignment.score,
                    "reasoning": result.difficulty_alignment.reasoning,
                    "issues": result.difficulty_alignment.issues,
                },
            },

            # Issues list
            "issues": [
                {
                    "id": issue.id,
                    "dimension": issue.dimension,
                    "snippet": issue.snippet,
                    "explanation": issue.explanation,
                    "severity": issue.severity,
                }
                for issue in result.issues
            ],

            # Hard fail info
            "hard_fail": {
                "failed": result.hard_fail.failed,
                "rules_triggered": result.hard_fail.rules_triggered,
                "details": result.hard_fail.details,
            } if result.hard_fail else None,

            # Timestamps
            "evaluated_at": datetime.utcnow(),
        }

        def do_insert():
            insert_result = collection.insert_one(doc)
            if not insert_result.acknowledged:
                raise PyMongoError("Write not acknowledged")
            return str(insert_result.inserted_id)

        result_id = self._db_write_with_retry(do_insert, f"store_result:{request_id}")

        # Update the request document to link to this evaluation
        self._link_evaluation_to_request(request_id, result_id)

        return result_id

    def _store_evaluation_error(
        self,
        run_id: str,
        request_id: str,
        node_id: Optional[str],
        request_payload: Dict[str, Any],
        response_data: Dict[str, Any],
        error: str,
        error_traceback: str,
    ) -> None:
        """Store a failed evaluation attempt."""
        db = self._get_db()
        collection = db[RESULTS_COLLECTION].with_options(write_concern=WRITE_CONCERN)

        doc = {
            "run_id": run_id,
            "request_id": request_id,
            "node_id": node_id,
            "request_payload": request_payload,
            "response_data": response_data,
            "passed": False,
            "overall_score": 0.0,
            "evaluation_error": error,
            "evaluation_error_traceback": error_traceback,
            "evaluated_at": datetime.utcnow(),
        }

        def do_insert():
            result = collection.insert_one(doc)
            if not result.acknowledged:
                raise PyMongoError("Write not acknowledged")

        try:
            self._db_write_with_retry(do_insert, f"store_eval_error:{request_id}")
        except Exception as e:
            logger.error(f"Failed to store evaluation error: {e}")

    def _link_evaluation_to_request(self, request_id: str, evaluation_id: str) -> None:
        """Link the evaluation result back to the request document."""
        db = self._get_db()
        collection = db[REQUESTS_COLLECTION]

        def do_update():
            result = collection.update_one(
                {"request_id": request_id},
                {"$set": {
                    "evaluated": True,
                    "evaluation_id": evaluation_id,
                    "evaluated_at": datetime.utcnow(),
                }}
            )
            return result.modified_count

        try:
            self._db_write_with_retry(do_update, f"link_eval:{request_id}")
        except Exception as e:
            logger.warning(f"Failed to link evaluation to request: {e}")

    def _create_run(
        self,
        course: str,
        config: Dict[str, Any],
    ) -> BenchmarkRun:
        """Create a new benchmark run record."""
        db = self._get_db()
        collection = db[RUNS_COLLECTION].with_options(write_concern=WRITE_CONCERN)

        run = BenchmarkRun(
            run_id=str(uuid.uuid4()),
            endpoint_url=self.endpoint_url,
            course=course,
            started_at=datetime.utcnow(),
            config=config,
        )

        doc = {
            "run_id": run.run_id,
            "endpoint_url": run.endpoint_url,
            "course": run.course,
            "started_at": run.started_at,
            "status": run.status,
            "config": run.config,
            "created_at": datetime.utcnow(),
        }

        def do_insert():
            result = collection.insert_one(doc)
            if not result.acknowledged:
                raise PyMongoError("Write not acknowledged")

        self._db_write_with_retry(do_insert, f"create_run:{run.run_id}")
        logger.info(f"Created benchmark run: {run.run_id}")

        return run

    def _update_run(self, run: BenchmarkRun) -> None:
        """Update a benchmark run record."""
        db = self._get_db()
        collection = db[RUNS_COLLECTION].with_options(write_concern=WRITE_CONCERN)

        update_doc = {
            "completed_at": run.completed_at,
            "total_requests": run.total_requests,
            "successful_requests": run.successful_requests,
            "failed_requests": run.failed_requests,
            "evaluated_count": run.evaluated_count,
            "evaluation_errors": run.evaluation_errors,
            "pass_count": run.pass_count,
            "fail_count": run.fail_count,
            "average_score": run.average_score,
            "average_latency_ms": run.average_latency_ms,
            "status": run.status,
            "error_message": run.error_message,
            "updated_at": datetime.utcnow(),
        }

        def do_update():
            result = collection.update_one(
                {"run_id": run.run_id},
                {"$set": update_doc}
            )
            return result.modified_count

        self._db_write_with_retry(do_update, f"update_run:{run.run_id}")

    async def run_benchmark(
        self,
        course: str = "APUSH",
        units: Optional[List[int]] = None,
        question_types: Optional[List[str]] = None,
        questions_per_unit: int = 10,
        sample_from_db: bool = True,
        evaluate: bool = True,
        progress_callback: Optional[Callable[[str, int, int], None]] = None,
    ) -> str:
        """
        Run a complete benchmark against the generation endpoint.

        Args:
            course: Course to benchmark (APUSH, APWH)
            units: Specific units (None = all)
            question_types: Question types to generate
            questions_per_unit: Questions per unit
            sample_from_db: Sample topics from MongoDB facts
            evaluate: Whether to evaluate responses
            progress_callback: Callback(stage, current, total)

        Returns:
            run_id for the benchmark run
        """
        self._ensure_indexes()

        # Create run record
        config = {
            "course": course,
            "units": units,
            "question_types": question_types or ["mcq"],
            "questions_per_unit": questions_per_unit,
            "concurrency": self.concurrency,
            "timeout": self.timeout,
            "sample_from_db": sample_from_db,
            "evaluate": evaluate,
        }
        run = self._create_run(course, config)

        try:
            # Generate requests
            if progress_callback:
                progress_callback("generating", 0, 0)

            requests = self._generate_requests_from_facts(
                course=course,
                units=units,
                question_types=question_types,
                questions_per_unit=questions_per_unit,
                sample_from_db=sample_from_db,
            )

            run.total_requests = len(requests)
            logger.info(f"Generated {len(requests)} requests for run {run.run_id}")

            # Update run with total count
            self._update_run(run)

            # Send requests in parallel
            def request_progress(current, total):
                if progress_callback:
                    progress_callback("requesting", current, total)

            responses = await self._send_requests_parallel(
                requests,
                progress_callback=request_progress,
            )

            # Build response lookup
            response_map = {r.request_id: r for r in responses}

            # Store request+response pairs and collect successful ones
            successful_responses = []
            latencies = []

            for req in requests:
                resp = response_map.get(req.request_id)
                if resp:
                    try:
                        self._store_request_response(run.run_id, req, resp)
                    except Exception as e:
                        logger.error(f"Failed to store request {req.request_id}: {e}")

                    latencies.append(resp.latency_ms)

                    if resp.response_data:
                        run.successful_requests += 1
                        successful_responses.append((req, resp))
                    else:
                        run.failed_requests += 1

            if latencies:
                run.average_latency_ms = sum(latencies) / len(latencies)

            logger.info(f"Run {run.run_id}: {run.successful_requests} successful, {run.failed_requests} failed")

            # Update run progress
            self._update_run(run)

            # Evaluate responses
            if evaluate and successful_responses:
                scores = []
                for i, (req, resp) in enumerate(successful_responses):
                    if progress_callback:
                        progress_callback("evaluating", i + 1, len(successful_responses))

                    try:
                        # Build question dict from response
                        # Handle wrapped responses: {success, request, output}
                        if "output" in resp.response_data and isinstance(resp.response_data["output"], dict):
                            question_dict = resp.response_data["output"].copy()
                        else:
                            question_dict = resp.response_data.copy()

                        question_dict["node_id"] = req.node_id

                        # Build evaluation request from generation request
                        eval_request = EvaluationRequest(
                            substandard_id=req.payload.get("topic", "UNKNOWN"),
                            node_id=req.node_id,
                            substandard_description=req.payload.get("learning_objective", ""),
                            difficulty=req.payload.get("difficulty", "medium"),
                            question_type=req.payload.get("type", "mcq"),
                        )

                        # Evaluate
                        result = evaluate_question(
                            question_dict=question_dict,
                            request=eval_request,
                        )

                        # Store result with full context
                        self._store_evaluation_result(
                            run_id=run.run_id,
                            request_id=req.request_id,
                            node_id=req.node_id,
                            request_payload=req.payload,
                            response_data=resp.response_data,
                            curriculum_fact=req.curriculum_fact,
                            result=result,
                        )

                        run.evaluated_count += 1
                        scores.append(result.overall_score)
                        if result.passed:
                            run.pass_count += 1
                        else:
                            run.fail_count += 1

                    except Exception as e:
                        logger.error(f"Evaluation error for {req.request_id}: {e}")
                        run.evaluation_errors += 1

                        # Store the error for debugging
                        self._store_evaluation_error(
                            run_id=run.run_id,
                            request_id=req.request_id,
                            node_id=req.node_id,
                            request_payload=req.payload,
                            response_data=resp.response_data,
                            error=str(e),
                            error_traceback=traceback.format_exc(),
                        )

                if scores:
                    run.average_score = sum(scores) / len(scores)

            # Mark run as completed
            run.completed_at = datetime.utcnow()
            run.status = "completed"
            self._update_run(run)

            logger.info(f"Benchmark run {run.run_id} completed")
            if run.evaluated_count:
                logger.info(f"Pass rate: {run.pass_count}/{run.evaluated_count} = {run.pass_count/run.evaluated_count:.1%}")

            return run.run_id

        except Exception as e:
            run.status = "failed"
            run.error_message = str(e)
            run.completed_at = datetime.utcnow()
            self._update_run(run)
            logger.error(f"Benchmark run {run.run_id} failed: {e}")
            raise

    def get_run_summary(self, run_id: str) -> Optional[Dict[str, Any]]:
        """Get summary of a benchmark run."""
        db = self._get_db()

        run = db[RUNS_COLLECTION].find_one({"run_id": run_id})
        if not run:
            return None

        # Get dimension pass rates from results
        results = list(db[RESULTS_COLLECTION].find(
            {"run_id": run_id, "evaluation_error": {"$exists": False}},
            {"dimensions": 1, "passed": 1, "overall_score": 1}
        ))

        dimension_stats = {}
        if results:
            dims = ["factual_accuracy", "curriculum_alignment", "cognitive_demand",
                    "distractor_quality", "explanation_quality", "clarity", "difficulty_alignment"]
            for dim in dims:
                passed = sum(1 for r in results if r.get("dimensions", {}).get(dim, {}).get("score", 0) == 1.0)
                dimension_stats[dim] = passed / len(results)

        return {
            "run_id": run_id,
            "endpoint_url": run.get("endpoint_url"),
            "course": run.get("course"),
            "started_at": run.get("started_at"),
            "completed_at": run.get("completed_at"),
            "status": run.get("status"),
            "error_message": run.get("error_message"),
            "total_requests": run.get("total_requests", 0),
            "successful_requests": run.get("successful_requests", 0),
            "failed_requests": run.get("failed_requests", 0),
            "evaluated_count": run.get("evaluated_count", 0),
            "evaluation_errors": run.get("evaluation_errors", 0),
            "pass_count": run.get("pass_count", 0),
            "fail_count": run.get("fail_count", 0),
            "pass_rate": run.get("pass_count", 0) / run.get("evaluated_count", 1) if run.get("evaluated_count") else 0,
            "average_score": run.get("average_score", 0),
            "average_latency_ms": run.get("average_latency_ms", 0),
            "dimension_pass_rates": dimension_stats,
            "config": run.get("config", {}),
        }

    def get_run_results(
        self,
        run_id: str,
        passed_only: bool = False,
        failed_only: bool = False,
        include_errors: bool = False,
    ) -> List[Dict[str, Any]]:
        """Get detailed results from a benchmark run."""
        db = self._get_db()

        query: Dict[str, Any] = {"run_id": run_id}

        if not include_errors:
            query["evaluation_error"] = {"$exists": False}

        if passed_only:
            query["passed"] = True
        elif failed_only:
            query["passed"] = False

        return list(db[RESULTS_COLLECTION].find(query, {"_id": 0}))

    def get_request_details(self, request_id: str) -> Optional[Dict[str, Any]]:
        """Get full details of a single request including evaluation."""
        db = self._get_db()

        request = db[REQUESTS_COLLECTION].find_one({"request_id": request_id}, {"_id": 0})
        if not request:
            return None

        result = db[RESULTS_COLLECTION].find_one({"request_id": request_id}, {"_id": 0})

        return {
            "request": request,
            "evaluation": result,
        }

    def list_runs(
        self,
        course: Optional[str] = None,
        status: Optional[str] = None,
        limit: int = 20,
    ) -> List[Dict[str, Any]]:
        """List recent benchmark runs."""
        db = self._get_db()

        query: Dict[str, Any] = {}
        if course:
            query["course"] = course
        if status:
            query["status"] = status

        runs = db[RUNS_COLLECTION].find(
            query,
            {"_id": 0}
        ).sort("started_at", -1).limit(limit)

        return list(runs)

    def delete_run(self, run_id: str) -> Dict[str, int]:
        """Delete a benchmark run and all associated data."""
        db = self._get_db()

        requests_deleted = db[REQUESTS_COLLECTION].delete_many({"run_id": run_id}).deleted_count
        results_deleted = db[RESULTS_COLLECTION].delete_many({"run_id": run_id}).deleted_count
        runs_deleted = db[RUNS_COLLECTION].delete_many({"run_id": run_id}).deleted_count

        return {
            "runs_deleted": runs_deleted,
            "requests_deleted": requests_deleted,
            "results_deleted": results_deleted,
        }


def run_benchmark_sync(
    endpoint_url: str,
    course: str = "APUSH",
    units: Optional[List[int]] = None,
    questions_per_unit: int = 10,
    concurrency: int = 5,
    verbose: bool = True,
) -> str:
    """
    Synchronous wrapper for running a benchmark.

    Returns run_id.
    """
    orchestrator = BenchmarkOrchestrator(
        endpoint_url=endpoint_url,
        concurrency=concurrency,
    )

    def progress(stage, current, total):
        if verbose:
            if stage == "generating":
                print("Generating requests from curriculum facts...")
            elif stage == "requesting":
                print(f"  Sending requests: {current}/{total}", end="\r")
            elif stage == "evaluating":
                print(f"  Evaluating: {current}/{total}", end="\r")

    run_id = asyncio.run(orchestrator.run_benchmark(
        course=course,
        units=units,
        questions_per_unit=questions_per_unit,
        progress_callback=progress if verbose else None,
    ))

    if verbose:
        print()
        summary = orchestrator.get_run_summary(run_id)
        if summary:
            print(f"\nBenchmark Run: {run_id}")
            print(f"Pass Rate: {summary['pass_rate']:.1%}")
            print(f"Average Score: {summary['average_score']:.2f}")
            print(f"Average Latency: {summary['average_latency_ms']:.0f}ms")

    return run_id
