"""Core evaluation components."""

from .models import (
    BenchmarkResult,
    DimensionScore,
    HardFailResult,
    QuestionType,
    Issue,
    EvaluationRequest,
)
from .evaluator import evaluate_question, evaluate_batch, evaluate_with_request
from .scorer import calculate_overall_score
from .hash import hash_question
from .curriculum import (
    build_curriculum_context,
    ConfidenceLevel,
    parse_substandard_id,
)
from .database import (
    get_mongo_client,
    get_facts_collection,
    close_connection,
    is_connected,
)
from .curriculum_db import (
    get_fact_by_node_id,
    get_facts_by_course_unit,
    get_facts_by_cluster,
    get_related_facts,
    search_facts,
    parse_node_id,
    get_fact_context_string,
    clear_cache,
)
from .orchestrator import (
    BenchmarkOrchestrator,
    run_benchmark_sync,
    GenerationRequest,
    GenerationResponse,
    BenchmarkRun,
)
from .pipeline import (
    PipelineBenchmark,
    PipelineConfig,
    PipelineStats,
    run_pipeline_benchmark,
    run_pipeline_sync,
)

__all__ = [
    # Models
    "BenchmarkResult",
    "DimensionScore",
    "HardFailResult",
    "QuestionType",
    "Issue",
    "EvaluationRequest",
    # Evaluator
    "evaluate_question",
    "evaluate_batch",
    "evaluate_with_request",
    # Scoring
    "calculate_overall_score",
    "hash_question",
    # Curriculum context
    "build_curriculum_context",
    "ConfidenceLevel",
    "parse_substandard_id",
    # MongoDB connection
    "get_mongo_client",
    "get_facts_collection",
    "close_connection",
    "is_connected",
    # Curriculum data access
    "get_fact_by_node_id",
    "get_facts_by_course_unit",
    "get_facts_by_cluster",
    "get_related_facts",
    "search_facts",
    "parse_node_id",
    "get_fact_context_string",
    "clear_cache",
    # Orchestrator
    "BenchmarkOrchestrator",
    "run_benchmark_sync",
    "GenerationRequest",
    "GenerationResponse",
    "BenchmarkRun",
    # Pipeline
    "PipelineBenchmark",
    "PipelineConfig",
    "PipelineStats",
    "run_pipeline_benchmark",
    "run_pipeline_sync",
]
