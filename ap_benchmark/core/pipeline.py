"""
Pipelined Benchmark - Parallel Generation & Evaluation

High-throughput benchmark system that:
1. Samples random standards from MongoDB
2. Generates questions across all difficulty levels
3. Randomly assigns question formats
4. Pipelines generation → evaluation with async queues
5. Processes everything in parallel for speed

Architecture:
    ┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
    │   Generator     │     │     Queue       │     │   Evaluator     │
    │   Workers (N)   │────▶│   (responses)   │────▶│   Workers (M)   │
    └─────────────────┘     └─────────────────┘     └─────────────────┘
           │                                                │
           ▼                                                ▼
    ┌─────────────────┐                           ┌─────────────────┐
    │  MongoDB:       │                           │  MongoDB:       │
    │  requests       │                           │  results        │
    └─────────────────┘                           └─────────────────┘

Usage:
    from ap_benchmark.core.pipeline import run_pipeline_benchmark

    run_id = await run_pipeline_benchmark(
        endpoint_url="http://192.168.1.10:8000/generate",
        num_standards=40,
        course="APUSH",
    )
"""

import asyncio
import logging
import random
import time
import traceback
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional, Callable, Tuple

import httpx
from pymongo import WriteConcern

from .database import get_database
from .evaluator import evaluate_question
from .models import BenchmarkResult, EvaluationRequest

logger = logging.getLogger(__name__)

# MongoDB collections
PIPELINE_RUNS = "pipeline_runs"
PIPELINE_REQUESTS = "pipeline_requests"
PIPELINE_RESULTS = "pipeline_results"

# Question formats to randomly choose from
QUESTION_FORMATS = ["mcq", "msq", "fill-in", "match"]

# Difficulty levels
DIFFICULTY_LEVELS = ["easy", "medium", "hard"]

# Write concern for durability
WRITE_CONCERN = WriteConcern(w=1, j=True)


@dataclass
class PipelineConfig:
    """Configuration for a pipeline benchmark run."""
    endpoint_url: str
    num_standards: int = 40
    course: str = "APUSH"

    # Parallelism settings
    generator_workers: int = 10  # Concurrent HTTP requests
    evaluator_workers: int = 5   # Concurrent evaluations (API-limited)

    # Timeouts
    request_timeout: float = 60.0
    retry_attempts: int = 2

    # Queue settings
    queue_size: int = 100  # Max items in evaluation queue


@dataclass
class GenerationTask:
    """A task for the generator workers."""
    task_id: str
    node_id: str
    curriculum_fact: Dict[str, Any]
    difficulty: str
    question_format: str
    payload: Dict[str, Any]


@dataclass
class EvaluationTask:
    """A task for the evaluator workers."""
    task_id: str
    node_id: str
    curriculum_fact: Dict[str, Any]
    request_payload: Dict[str, Any]
    response_data: Dict[str, Any]
    latency_ms: float


@dataclass
class PipelineStats:
    """Live statistics for the pipeline."""
    run_id: str
    started_at: datetime

    # Generation stats
    total_tasks: int = 0
    generated: int = 0
    generation_errors: int = 0

    # Evaluation stats
    evaluated: int = 0
    evaluation_errors: int = 0
    passed: int = 0
    failed: int = 0

    # Score tracking
    total_score: float = 0.0
    recent_scores: List[float] = field(default_factory=list)
    consecutive_zero_threshold: int = 5  # Stop after this many consecutive 0s

    # Timing
    total_latency_ms: float = 0.0

    @property
    def generation_progress(self) -> float:
        return self.generated / self.total_tasks if self.total_tasks else 0

    @property
    def evaluation_progress(self) -> float:
        expected = self.generated - self.generation_errors
        return self.evaluated / expected if expected else 0

    @property
    def pass_rate(self) -> float:
        return self.passed / self.evaluated if self.evaluated else 0

    @property
    def avg_score(self) -> float:
        return self.total_score / self.evaluated if self.evaluated else 0

    @property
    def avg_latency_ms(self) -> float:
        return self.total_latency_ms / self.generated if self.generated else 0

    def should_early_stop(self) -> bool:
        """Check if we should stop due to consecutive zeros."""
        if len(self.recent_scores) < self.consecutive_zero_threshold:
            return False
        # Check last N scores are all 0
        return all(s == 0.0 for s in self.recent_scores[-self.consecutive_zero_threshold:])


class PipelineBenchmark:
    """
    Pipelined benchmark with parallel generation and evaluation.

    Uses async queues to pipeline work:
    - Generator workers fetch from endpoint, push to queue
    - Evaluator workers pull from queue, evaluate, store
    """

    def __init__(self, config: PipelineConfig):
        self.config = config
        self.stats: Optional[PipelineStats] = None
        self._eval_queue: Optional[asyncio.Queue] = None
        self._shutdown = False

    def _get_db(self):
        """Get MongoDB database."""
        db = get_database()
        if db is None:
            raise RuntimeError("MongoDB required. Set MONGODB_URI.")
        return db

    def _ensure_indexes(self):
        """Create MongoDB indexes."""
        db = self._get_db()

        db[PIPELINE_RUNS].create_index("run_id", unique=True)
        db[PIPELINE_RUNS].create_index("started_at")

        db[PIPELINE_REQUESTS].create_index("run_id")
        db[PIPELINE_REQUESTS].create_index("task_id", unique=True)
        db[PIPELINE_REQUESTS].create_index([("run_id", 1), ("status", 1)])

        db[PIPELINE_RESULTS].create_index("run_id")
        db[PIPELINE_RESULTS].create_index("task_id", unique=True)
        db[PIPELINE_RESULTS].create_index([("run_id", 1), ("passed", 1)])

    def _sample_standards(self) -> List[Dict[str, Any]]:
        """Sample random standards from MongoDB."""
        db = self._get_db()

        # Use aggregation with $sample for random selection
        pipeline = [
            {"$match": {"course": self.config.course}},
            {"$sample": {"size": self.config.num_standards}}
        ]

        facts = list(db["facts"].aggregate(pipeline))

        # Remove MongoDB _id
        for fact in facts:
            fact.pop("_id", None)

        logger.info(f"Sampled {len(facts)} standards from {self.config.course}")
        return facts

    def _create_tasks(self, facts: List[Dict[str, Any]]) -> List[GenerationTask]:
        """Create generation tasks from sampled facts."""
        tasks = []

        for fact in facts:
            node_id = fact.get("node_id", str(uuid.uuid4()))

            # Create one task per difficulty level
            for difficulty in DIFFICULTY_LEVELS:
                # Randomly select format
                question_format = random.choice(QUESTION_FORMATS)

                task_id = str(uuid.uuid4())

                payload = {
                    "type": question_format,
                    "topic": fact.get("cluster", ""),
                    "course": self.config.course,
                    "unit": fact.get("unit"),
                    "node_id": node_id,
                    "learning_objective": fact.get("learning_objective", ""),
                    "statement": fact.get("statement", ""),
                    "difficulty": difficulty,
                }

                tasks.append(GenerationTask(
                    task_id=task_id,
                    node_id=node_id,
                    curriculum_fact=fact,
                    difficulty=difficulty,
                    question_format=question_format,
                    payload=payload,
                ))

        logger.info(f"Created {len(tasks)} generation tasks")
        return tasks

    def _create_run(self, num_tasks: int) -> str:
        """Create pipeline run record."""
        db = self._get_db()
        run_id = str(uuid.uuid4())

        db[PIPELINE_RUNS].with_options(write_concern=WRITE_CONCERN).insert_one({
            "run_id": run_id,
            "endpoint_url": self.config.endpoint_url,
            "course": self.config.course,
            "num_standards": self.config.num_standards,
            "total_tasks": num_tasks,
            "config": {
                "generator_workers": self.config.generator_workers,
                "evaluator_workers": self.config.evaluator_workers,
                "formats": QUESTION_FORMATS,
                "difficulties": DIFFICULTY_LEVELS,
            },
            "started_at": datetime.utcnow(),
            "status": "running",
        })

        return run_id

    def _update_run(self):
        """Update run record with current stats."""
        if not self.stats:
            return

        db = self._get_db()
        db[PIPELINE_RUNS].update_one(
            {"run_id": self.stats.run_id},
            {"$set": {
                "generated": self.stats.generated,
                "generation_errors": self.stats.generation_errors,
                "evaluated": self.stats.evaluated,
                "evaluation_errors": self.stats.evaluation_errors,
                "passed": self.stats.passed,
                "failed": self.stats.failed,
                "pass_rate": self.stats.pass_rate,
                "avg_score": self.stats.avg_score,
                "avg_latency_ms": self.stats.avg_latency_ms,
                "updated_at": datetime.utcnow(),
            }}
        )

    def _finalize_run(self, status: str = "completed", error: str = None):
        """Finalize the run record."""
        if not self.stats:
            return

        # Check if early stopped
        if self.stats.should_early_stop():
            status = "early_stopped"

        db = self._get_db()
        update = {
            "status": status,
            "completed_at": datetime.utcnow(),
            "generated": self.stats.generated,
            "generation_errors": self.stats.generation_errors,
            "evaluated": self.stats.evaluated,
            "evaluation_errors": self.stats.evaluation_errors,
            "passed": self.stats.passed,
            "failed": self.stats.failed,
            "pass_rate": self.stats.pass_rate,
            "avg_score": self.stats.avg_score,
            "avg_latency_ms": self.stats.avg_latency_ms,
        }
        if error:
            update["error"] = error
        if self.stats.should_early_stop():
            update["early_stop_reason"] = f"Consecutive {self.stats.consecutive_zero_threshold} zero scores"

        db[PIPELINE_RUNS].update_one(
            {"run_id": self.stats.run_id},
            {"$set": update}
        )

    def _store_request(self, task: GenerationTask, response_data: Optional[Dict],
                       error: Optional[str], latency_ms: float):
        """Store generation request/response."""
        db = self._get_db()

        db[PIPELINE_REQUESTS].with_options(write_concern=WRITE_CONCERN).insert_one({
            "run_id": self.stats.run_id,
            "task_id": task.task_id,
            "node_id": task.node_id,
            "curriculum_fact": task.curriculum_fact,
            "request_payload": task.payload,
            "difficulty": task.difficulty,
            "question_format": task.question_format,
            "response_data": response_data,
            "error": error,
            "latency_ms": latency_ms,
            "status": "success" if response_data else "error",
            "created_at": datetime.utcnow(),
        })

    def _store_result(self, task: EvaluationTask, result: Optional[BenchmarkResult],
                      error: Optional[str]):
        """Store evaluation result."""
        db = self._get_db()

        doc = {
            "run_id": self.stats.run_id,
            "task_id": task.task_id,
            "node_id": task.node_id,
            "curriculum_fact": task.curriculum_fact,
            "request_payload": task.request_payload,
            "response_data": task.response_data,
            "generation_latency_ms": task.latency_ms,
            "evaluated_at": datetime.utcnow(),
        }

        if result:
            doc.update({
                "passed": result.passed,
                "overall_score": result.overall_score,
                "question_hash": result.question_hash,
                "prompt_version": result.prompt_version,
                "critical_failures": result.critical_failures,
                "non_critical_failures": result.non_critical_failures,
                "dimensions": {
                    "factual_accuracy": {"score": result.factual_accuracy.score, "reasoning": result.factual_accuracy.reasoning},
                    "curriculum_alignment": {"score": result.curriculum_alignment.score, "reasoning": result.curriculum_alignment.reasoning},
                    "cognitive_demand": {"score": result.cognitive_demand.score, "reasoning": result.cognitive_demand.reasoning},
                    "distractor_quality": {"score": result.distractor_quality.score, "reasoning": result.distractor_quality.reasoning},
                    "explanation_quality": {"score": result.explanation_quality.score, "reasoning": result.explanation_quality.reasoning},
                    "clarity": {"score": result.clarity.score, "reasoning": result.clarity.reasoning},
                    "difficulty_alignment": {"score": result.difficulty_alignment.score, "reasoning": result.difficulty_alignment.reasoning},
                },
                "issues": [{"id": i.id, "dimension": i.dimension, "snippet": i.snippet, "explanation": i.explanation} for i in result.issues],
                "hard_fail": result.hard_fail.model_dump() if result.hard_fail else None,
            })

        if error:
            doc["evaluation_error"] = error
            doc["passed"] = False
            doc["overall_score"] = 0.0

        db[PIPELINE_RESULTS].with_options(write_concern=WRITE_CONCERN).insert_one(doc)

    async def _generator_worker(
        self,
        worker_id: int,
        client: httpx.AsyncClient,
        task_queue: asyncio.Queue,
        semaphore: asyncio.Semaphore,
    ):
        """Worker that generates questions from endpoint."""
        while not self._shutdown:
            try:
                # Get task with timeout
                try:
                    task: GenerationTask = await asyncio.wait_for(
                        task_queue.get(), timeout=1.0
                    )
                except asyncio.TimeoutError:
                    continue

                start_time = time.perf_counter()
                response_data = None
                error = None

                # Make request with semaphore for rate limiting
                async with semaphore:
                    for attempt in range(self.config.retry_attempts + 1):
                        try:
                            response = await client.post(
                                self.config.endpoint_url,
                                json=task.payload,
                                timeout=self.config.request_timeout,
                            )
                            response.raise_for_status()
                            response_data = response.json()
                            break
                        except Exception as e:
                            if attempt == self.config.retry_attempts:
                                error = f"{type(e).__name__}: {str(e)}"
                            else:
                                await asyncio.sleep(1 * (attempt + 1))

                latency_ms = (time.perf_counter() - start_time) * 1000

                # Update stats
                self.stats.generated += 1
                self.stats.total_latency_ms += latency_ms

                if error:
                    self.stats.generation_errors += 1

                # Store request
                self._store_request(task, response_data, error, latency_ms)

                # Queue for evaluation if successful
                if response_data:
                    eval_task = EvaluationTask(
                        task_id=task.task_id,
                        node_id=task.node_id,
                        curriculum_fact=task.curriculum_fact,
                        request_payload=task.payload,
                        response_data=response_data,
                        latency_ms=latency_ms,
                    )
                    await self._eval_queue.put(eval_task)

                task_queue.task_done()

            except Exception as e:
                logger.error(f"Generator worker {worker_id} error: {e}")

    async def _evaluator_worker(
        self,
        worker_id: int,
        semaphore: asyncio.Semaphore,
    ):
        """Worker that evaluates generated questions."""
        while not self._shutdown:
            try:
                # Get task with timeout
                try:
                    task: EvaluationTask = await asyncio.wait_for(
                        self._eval_queue.get(), timeout=1.0
                    )
                except asyncio.TimeoutError:
                    continue

                result = None
                error = None

                async with semaphore:
                    try:
                        # Build question dict - handle wrapped responses
                        # Some endpoints wrap response in {success, request, output}
                        if "output" in task.response_data and isinstance(task.response_data["output"], dict):
                            question_dict = task.response_data["output"].copy()
                        else:
                            question_dict = task.response_data.copy()

                        question_dict["node_id"] = task.node_id

                        # Build evaluation request
                        eval_request = EvaluationRequest(
                            substandard_id=task.request_payload.get("topic", "UNKNOWN"),
                            node_id=task.node_id,
                            substandard_description=task.request_payload.get("learning_objective", ""),
                            difficulty=task.request_payload.get("difficulty", "medium"),
                            question_type=task.request_payload.get("type", "mcq"),
                        )

                        # Run evaluation (synchronous, but wrapped)
                        result = await asyncio.get_event_loop().run_in_executor(
                            None,
                            lambda: evaluate_question(
                                question_dict=question_dict,
                                request=eval_request,
                            )
                        )

                    except Exception as e:
                        error = f"{type(e).__name__}: {str(e)}"
                        logger.error(f"Evaluation error: {e}")

                # Update stats
                self.stats.evaluated += 1
                if error:
                    self.stats.evaluation_errors += 1
                    self.stats.recent_scores.append(0.0)
                elif result:
                    score = result.overall_score
                    self.stats.total_score += score
                    self.stats.recent_scores.append(score)
                    if result.passed:
                        self.stats.passed += 1
                    else:
                        self.stats.failed += 1

                # Store result
                self._store_result(task, result, error)

                # Check for early stopping
                if self.stats.should_early_stop():
                    logger.warning(f"Early stopping: {self.stats.consecutive_zero_threshold} consecutive 0 scores")
                    self._shutdown = True
                    return

                self._eval_queue.task_done()

            except Exception as e:
                logger.error(f"Evaluator worker {worker_id} error: {e}")

    async def run(
        self,
        progress_callback: Optional[Callable[[PipelineStats], None]] = None,
    ) -> str:
        """
        Run the pipeline benchmark.

        Returns run_id.
        """
        self._ensure_indexes()
        self._shutdown = False

        # Sample standards and create tasks
        facts = self._sample_standards()
        if not facts:
            raise ValueError(f"No standards found for course {self.config.course}")

        tasks = self._create_tasks(facts)

        # Create run record
        run_id = self._create_run(len(tasks))

        # Initialize stats
        self.stats = PipelineStats(
            run_id=run_id,
            started_at=datetime.utcnow(),
            total_tasks=len(tasks),
        )

        logger.info(f"Starting pipeline run {run_id} with {len(tasks)} tasks")

        # Create queues
        task_queue = asyncio.Queue()
        self._eval_queue = asyncio.Queue(maxsize=self.config.queue_size)

        # Load tasks into queue
        for task in tasks:
            await task_queue.put(task)

        # Create semaphores for rate limiting
        gen_semaphore = asyncio.Semaphore(self.config.generator_workers)
        eval_semaphore = asyncio.Semaphore(self.config.evaluator_workers)

        # Start workers
        async with httpx.AsyncClient() as client:
            generator_workers = [
                asyncio.create_task(
                    self._generator_worker(i, client, task_queue, gen_semaphore)
                )
                for i in range(self.config.generator_workers)
            ]

            evaluator_workers = [
                asyncio.create_task(
                    self._evaluator_worker(i, eval_semaphore)
                )
                for i in range(self.config.evaluator_workers)
            ]

            # Progress reporter
            async def report_progress():
                while not self._shutdown:
                    await asyncio.sleep(2)
                    self._update_run()
                    if progress_callback:
                        progress_callback(self.stats)

            progress_task = asyncio.create_task(report_progress())

            try:
                # Wait for all generation tasks to complete
                await task_queue.join()
                logger.info("All generation tasks completed")

                # Wait for evaluation queue to drain
                await self._eval_queue.join()
                logger.info("All evaluation tasks completed")

            finally:
                # Shutdown workers
                self._shutdown = True
                progress_task.cancel()

                for w in generator_workers + evaluator_workers:
                    w.cancel()

                await asyncio.gather(*generator_workers, *evaluator_workers, return_exceptions=True)

        # Finalize
        self._finalize_run("completed")

        logger.info(f"Pipeline run {run_id} completed")
        logger.info(f"Generated: {self.stats.generated}, Evaluated: {self.stats.evaluated}")
        logger.info(f"Pass rate: {self.stats.pass_rate:.1%}")

        return run_id

    def get_run_summary(self, run_id: str) -> Optional[Dict[str, Any]]:
        """Get summary of a pipeline run."""
        db = self._get_db()

        run = db[PIPELINE_RUNS].find_one({"run_id": run_id}, {"_id": 0})
        if not run:
            return None

        # Get dimension stats
        results = list(db[PIPELINE_RESULTS].find(
            {"run_id": run_id, "evaluation_error": {"$exists": False}},
            {"dimensions": 1, "passed": 1}
        ))

        dimension_stats = {}
        if results:
            dims = ["factual_accuracy", "curriculum_alignment", "cognitive_demand",
                    "distractor_quality", "explanation_quality", "clarity", "difficulty_alignment"]
            for dim in dims:
                passed = sum(1 for r in results if r.get("dimensions", {}).get(dim, {}).get("score", 0) == 1.0)
                dimension_stats[dim] = passed / len(results)

        # Get breakdown by difficulty and format
        difficulty_stats = {}
        format_stats = {}

        for diff in DIFFICULTY_LEVELS:
            diff_results = list(db[PIPELINE_RESULTS].find(
                {"run_id": run_id, "request_payload.difficulty": diff, "passed": {"$exists": True}},
                {"passed": 1}
            ))
            if diff_results:
                difficulty_stats[diff] = sum(1 for r in diff_results if r.get("passed")) / len(diff_results)

        for fmt in QUESTION_FORMATS:
            fmt_results = list(db[PIPELINE_RESULTS].find(
                {"run_id": run_id, "request_payload.type": fmt, "passed": {"$exists": True}},
                {"passed": 1}
            ))
            if fmt_results:
                format_stats[fmt] = sum(1 for r in fmt_results if r.get("passed")) / len(fmt_results)

        run["dimension_pass_rates"] = dimension_stats
        run["difficulty_pass_rates"] = difficulty_stats
        run["format_pass_rates"] = format_stats

        return run

    def get_failed_results(self, run_id: str, limit: int = 50) -> List[Dict[str, Any]]:
        """Get failed evaluation results."""
        db = self._get_db()
        return list(db[PIPELINE_RESULTS].find(
            {"run_id": run_id, "passed": False},
            {"_id": 0}
        ).limit(limit))

    def list_runs(self, limit: int = 20) -> List[Dict[str, Any]]:
        """List recent pipeline runs."""
        db = self._get_db()
        return list(db[PIPELINE_RUNS].find(
            {},
            {"_id": 0}
        ).sort("started_at", -1).limit(limit))


async def run_pipeline_benchmark(
    endpoint_url: str,
    num_standards: int = 40,
    course: str = "APUSH",
    generator_workers: int = 10,
    evaluator_workers: int = 5,
    verbose: bool = True,
) -> str:
    """
    Run a pipeline benchmark.

    Args:
        endpoint_url: Generation endpoint URL
        num_standards: Number of random standards to sample
        course: Course to benchmark (APUSH, APWH)
        generator_workers: Concurrent generation requests
        evaluator_workers: Concurrent evaluations
        verbose: Print progress

    Returns:
        run_id
    """
    config = PipelineConfig(
        endpoint_url=endpoint_url,
        num_standards=num_standards,
        course=course,
        generator_workers=generator_workers,
        evaluator_workers=evaluator_workers,
    )

    pipeline = PipelineBenchmark(config)

    def progress(stats: PipelineStats):
        if verbose:
            gen_pct = stats.generation_progress * 100
            eval_pct = stats.evaluation_progress * 100
            print(
                f"\rGenerated: {stats.generated}/{stats.total_tasks} ({gen_pct:.0f}%) | "
                f"Evaluated: {stats.evaluated}/{stats.generated - stats.generation_errors} ({eval_pct:.0f}%) | "
                f"Avg score: {stats.avg_score:.2f} | "
                f"Pass rate: {stats.pass_rate:.1%}",
                end="", flush=True
            )

    if verbose:
        print(f"Pipeline Benchmark")
        print(f"  Endpoint: {endpoint_url}")
        print(f"  Course: {course}")
        print(f"  Standards: {num_standards}")
        print(f"  Tasks: {num_standards * 3} (3 difficulties × {num_standards} standards)")
        print(f"  Formats: {QUESTION_FORMATS}")
        print(f"  Workers: {generator_workers} generators, {evaluator_workers} evaluators")
        print()

    run_id = await pipeline.run(progress_callback=progress if verbose else None)

    if verbose:
        print()  # Newline after progress
        print()
        summary = pipeline.get_run_summary(run_id)
        if summary:
            print("=" * 60)
            print(f"Pipeline Run Complete: {run_id}")
            print("=" * 60)
            print(f"Status: {summary.get('status')}")
            if summary.get('early_stop_reason'):
                print(f"Early Stop: {summary.get('early_stop_reason')}")
            print(f"Generated: {summary.get('generated')}")
            print(f"Evaluated: {summary.get('evaluated')}")
            print(f"Passed: {summary.get('passed')}")
            print(f"Failed: {summary.get('failed')}")
            print(f"Average Score: {summary.get('avg_score', 0):.3f}")
            print(f"Pass Rate: {summary.get('pass_rate', 0):.1%}")
            print(f"Avg Latency: {summary.get('avg_latency_ms', 0):.0f}ms")
            print()
            print("Pass Rate by Difficulty:")
            for diff, rate in summary.get("difficulty_pass_rates", {}).items():
                print(f"  {diff}: {rate:.1%}")
            print()
            print("Pass Rate by Format:")
            for fmt, rate in summary.get("format_pass_rates", {}).items():
                print(f"  {fmt}: {rate:.1%}")
            print()
            print("Dimension Pass Rates:")
            for dim, rate in summary.get("dimension_pass_rates", {}).items():
                print(f"  {dim}: {rate:.1%}")

    return run_id


def run_pipeline_sync(
    endpoint_url: str,
    num_standards: int = 40,
    course: str = "APUSH",
    verbose: bool = True,
) -> str:
    """Synchronous wrapper for pipeline benchmark."""
    return asyncio.run(run_pipeline_benchmark(
        endpoint_url=endpoint_url,
        num_standards=num_standards,
        course=course,
        verbose=verbose,
    ))
