#!/usr/bin/env python3
"""
AP Benchmark CLI - Independent Evaluation System

A deterministic, reproducible benchmark for AP Social Studies questions.
Uses Claude as an independent evaluator (no self-grading).

Usage:
    # Evaluate questions from JSON file
    python -m ap_benchmark.benchmark --input questions.json

    # Run calibration check
    python -m ap_benchmark.benchmark --calibrate

    # Benchmark a generation endpoint
    python -m ap_benchmark.benchmark --endpoint http://192.168.1.10:8000/generate --course APUSH

    # Pipeline benchmark (40 random standards, 3 difficulties each, random formats)
    python -m ap_benchmark.benchmark --pipeline http://192.168.1.10:8000/generate --standards 40

    # List recent benchmark runs
    python -m ap_benchmark.benchmark --list-runs

    # View benchmark run results
    python -m ap_benchmark.benchmark --run-id <run_id>

    # Output as markdown
    python -m ap_benchmark.benchmark --input questions.json --format markdown

    # Output as CSV
    python -m ap_benchmark.benchmark --input questions.json --format csv
"""

import argparse
import json
import sys
import csv
from datetime import datetime
from io import StringIO
from pathlib import Path
from typing import List, Dict, Any, Optional

from .core.models import BenchmarkResult, BatchResult, QuestionType
from .core.evaluator import evaluate_question, evaluate_batch
from .core.scorer import PASS_THRESHOLD, explain_score
from .calibration.validator import validate_evaluator, CalibrationResult
from .hard_fail.checker import check_hard_fails
from . import __version__, __prompt_version__


def load_questions(input_path: str) -> List[Dict[str, Any]]:
    """Load questions from JSON file."""
    path = Path(input_path)
    if not path.exists():
        raise FileNotFoundError(f"Input file not found: {input_path}")

    with open(path, 'r') as f:
        data = json.load(f)

    # Handle both list and object with 'questions' key
    if isinstance(data, list):
        questions = data
    elif isinstance(data, dict) and 'questions' in data:
        questions = data['questions']
    else:
        raise ValueError("Input must be a JSON array or object with 'questions' key")

    # Ensure each question has an ID
    for i, q in enumerate(questions):
        if 'id' not in q:
            q['id'] = f"q_{i+1}"

    return questions


def format_json_output(results: Dict[str, BenchmarkResult], questions: List[Dict]) -> str:
    """Format results as JSON."""
    output = {
        "benchmark_version": __version__,
        "prompt_version": __prompt_version__,
        "timestamp": datetime.now().isoformat(),
        "pass_threshold": PASS_THRESHOLD,
        "summary": {
            "total": len(results),
            "passed": sum(1 for r in results.values() if r.passed),
            "failed": sum(1 for r in results.values() if not r.passed),
            "pass_rate": sum(1 for r in results.values() if r.passed) / len(results) if results else 0,
            "average_score": sum(r.overall_score for r in results.values()) / len(results) if results else 0,
        },
        "results": {}
    }

    for qid, result in results.items():
        output["results"][qid] = {
            "passed": result.passed,
            "overall_score": result.overall_score,
            "question_hash": result.question_hash,
            "hard_fail": result.hard_fail.model_dump() if result.hard_fail else None,
            "issues": [issue.model_dump() for issue in result.issues],
            "dimensions": {
                "factual_accuracy": result.factual_accuracy.model_dump(),
                "curriculum_alignment": result.curriculum_alignment.model_dump(),
                "cognitive_demand": result.cognitive_demand.model_dump(),
                "distractor_quality": result.distractor_quality.model_dump(),
                "explanation_quality": result.explanation_quality.model_dump(),
                "clarity": result.clarity.model_dump(),
                "difficulty_alignment": result.difficulty_alignment.model_dump(),
            },
            "critical_failures": result.critical_failures,
            "non_critical_failures": result.non_critical_failures,
        }

    return json.dumps(output, indent=2)


def format_markdown_output(results: Dict[str, BenchmarkResult], questions: List[Dict]) -> str:
    """Format results as Markdown report."""
    lines = [
        "# AP Benchmark Report",
        "",
        f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        f"**Benchmark Version:** {__version__}",
        f"**Prompt Version:** {__prompt_version__}",
        f"**Pass Threshold:** {PASS_THRESHOLD}",
        "",
        "## Summary",
        "",
    ]

    total = len(results)
    passed = sum(1 for r in results.values() if r.passed)
    failed = total - passed
    pass_rate = passed / total if total > 0 else 0
    avg_score = sum(r.overall_score for r in results.values()) / total if total > 0 else 0

    lines.extend([
        f"| Metric | Value |",
        f"|--------|-------|",
        f"| Total Questions | {total} |",
        f"| Passed | {passed} |",
        f"| Failed | {failed} |",
        f"| Pass Rate | {pass_rate:.1%} |",
        f"| Average Score | {avg_score:.2f} |",
        "",
        "## Results by Question",
        "",
    ])

    # Build question lookup
    question_lookup = {q.get('id', f'q_{i}'): q for i, q in enumerate(questions)}

    for qid, result in results.items():
        status = "PASS" if result.passed else "FAIL"
        emoji = "" if result.passed else ""

        lines.append(f"### {qid} - {status} {emoji}")
        lines.append("")
        lines.append(f"**Score:** {result.overall_score:.2f}")
        lines.append("")

        # Show question preview
        q = question_lookup.get(qid, {})
        question_text = q.get('question', '')[:100]
        if len(q.get('question', '')) > 100:
            question_text += "..."
        lines.append(f"**Question:** {question_text}")
        lines.append("")

        # Hard fail info
        if result.hard_fail and result.hard_fail.failed:
            lines.append("**Hard Fail Rules Triggered:**")
            for rule in result.hard_fail.rules_triggered:
                lines.append(f"- {rule}")
            lines.append("")

        # Dimension scores
        lines.append("| Dimension | Score | Status |")
        lines.append("|-----------|-------|--------|")

        dimensions = [
            ("Factual Accuracy", result.factual_accuracy, True),
            ("Curriculum Alignment", result.curriculum_alignment, True),
            ("Cognitive Demand", result.cognitive_demand, False),
            ("Distractor Quality", result.distractor_quality, False),
            ("Explanation Quality", result.explanation_quality, False),
            ("Clarity", result.clarity, False),
            ("Difficulty Alignment", result.difficulty_alignment, False),
        ]

        for name, dim, is_critical in dimensions:
            score = dim.score
            status = "PASS" if score == 1.0 else "FAIL"
            critical_marker = " (Critical)" if is_critical else ""
            lines.append(f"| {name}{critical_marker} | {score:.1f} | {status} |")

        lines.append("")

        # Issues
        if result.issues:
            lines.append("**Issues Identified:**")
            for issue in result.issues:
                lines.append(f"- **{issue.id}** ({issue.dimension}): {issue.explanation}")
            lines.append("")

        lines.append("---")
        lines.append("")

    return "\n".join(lines)


def format_csv_output(results: Dict[str, BenchmarkResult], questions: List[Dict]) -> str:
    """Format results as CSV."""
    output = StringIO()
    writer = csv.writer(output)

    # Header
    writer.writerow([
        "question_id",
        "passed",
        "overall_score",
        "critical_failures",
        "non_critical_failures",
        "factual_accuracy",
        "curriculum_alignment",
        "cognitive_demand",
        "distractor_quality",
        "explanation_quality",
        "clarity",
        "difficulty_alignment",
        "hard_fail",
        "issues_count",
    ])

    # Data rows
    for qid, result in results.items():
        writer.writerow([
            qid,
            result.passed,
            result.overall_score,
            result.critical_failures,
            result.non_critical_failures,
            result.factual_accuracy.score,
            result.curriculum_alignment.score,
            result.cognitive_demand.score,
            result.distractor_quality.score,
            result.explanation_quality.score,
            result.clarity.score,
            result.difficulty_alignment.score,
            result.hard_fail.failed if result.hard_fail else False,
            len(result.issues),
        ])

    return output.getvalue()


def format_summary_output(results: Dict[str, BenchmarkResult]) -> str:
    """Format brief summary output."""
    total = len(results)
    passed = sum(1 for r in results.values() if r.passed)
    failed = total - passed
    pass_rate = passed / total if total > 0 else 0
    avg_score = sum(r.overall_score for r in results.values()) / total if total > 0 else 0

    hard_fails = sum(1 for r in results.values() if r.hard_fail and r.hard_fail.failed)

    lines = [
        "AP Benchmark Results",
        "=" * 40,
        f"Total:       {total}",
        f"Passed:      {passed} ({pass_rate:.1%})",
        f"Failed:      {failed}",
        f"Hard Fails:  {hard_fails}",
        f"Avg Score:   {avg_score:.2f}",
        "",
        "Dimension Pass Rates:",
    ]

    # Calculate dimension pass rates
    if results:
        dimensions = [
            "factual_accuracy",
            "curriculum_alignment",
            "cognitive_demand",
            "distractor_quality",
            "explanation_quality",
            "clarity",
            "difficulty_alignment",
        ]

        for dim in dimensions:
            dim_passed = sum(1 for r in results.values() if getattr(r, dim).score == 1.0)
            dim_rate = dim_passed / total
            lines.append(f"  {dim}: {dim_rate:.1%}")

    return "\n".join(lines)


def run_benchmark(
    input_path: str,
    output_format: str = "json",
    output_path: Optional[str] = None,
    verbose: bool = False,
) -> int:
    """
    Run benchmark on questions from file.

    Returns exit code (0 = success, 1 = failure).
    """
    # Load questions
    if verbose:
        print(f"Loading questions from {input_path}...")

    questions = load_questions(input_path)

    if verbose:
        print(f"Loaded {len(questions)} questions")
        print("Evaluating...")

    # Progress callback
    def progress(current, total):
        if verbose:
            pct = current / total * 100
            print(f"  [{current}/{total}] {pct:.0f}%", end="\r")

    # Evaluate all questions
    results = evaluate_batch(
        questions=questions,
        progress_callback=progress if verbose else None,
    )

    if verbose:
        print()  # New line after progress

    # Format output
    formatters = {
        "json": format_json_output,
        "markdown": format_markdown_output,
        "md": format_markdown_output,
        "csv": format_csv_output,
        "summary": format_summary_output,
    }

    formatter = formatters.get(output_format, format_json_output)

    if output_format == "summary":
        output = formatter(results)
    else:
        output = formatter(results, questions)

    # Write output
    if output_path:
        with open(output_path, 'w') as f:
            f.write(output)
        if verbose:
            print(f"Results written to {output_path}")
    else:
        print(output)

    # Return exit code based on pass rate
    passed = sum(1 for r in results.values() if r.passed)
    pass_rate = passed / len(results) if results else 0

    return 0 if pass_rate >= 0.8 else 1


def run_calibration(verbose: bool = True) -> int:
    """
    Run calibration check.

    Returns exit code (0 = passed, 1 = failed).
    """
    print("Running calibration check...")
    print(f"Benchmark Version: {__version__}")
    print(f"Prompt Version: {__prompt_version__}")
    print()

    result = validate_evaluator(
        required_accuracy=0.95,
        verbose=verbose,
    )

    return 0 if result.passed else 1


def run_endpoint_benchmark(
    endpoint_url: str,
    course: str = "APUSH",
    units: Optional[List[int]] = None,
    questions_per_unit: int = 10,
    concurrency: int = 5,
    verbose: bool = True,
) -> int:
    """
    Run benchmark against a generation endpoint.

    Returns exit code (0 = success, 1 = failure).
    """
    from .core.orchestrator import BenchmarkOrchestrator
    import asyncio

    print(f"Benchmarking endpoint: {endpoint_url}")
    print(f"Course: {course}")
    print(f"Units: {units or 'all'}")
    print(f"Questions per unit: {questions_per_unit}")
    print(f"Concurrency: {concurrency}")
    print()

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
                print(f"  Evaluating responses: {current}/{total}", end="\r")

    try:
        run_id = asyncio.run(orchestrator.run_benchmark(
            course=course,
            units=units,
            questions_per_unit=questions_per_unit,
            progress_callback=progress if verbose else None,
        ))

        print()  # Newline after progress
        print()

        # Print summary
        summary = orchestrator.get_run_summary(run_id)
        if summary:
            print("=" * 50)
            print(f"Benchmark Run: {run_id}")
            print("=" * 50)
            print(f"Status: {summary['status']}")
            print(f"Total Requests: {summary['total_requests']}")
            print(f"Successful: {summary['successful_requests']}")
            print(f"Failed: {summary['failed_requests']}")
            print()
            print(f"Evaluated: {summary['evaluated_count']}")
            print(f"Passed: {summary['pass_count']}")
            print(f"Failed: {summary['fail_count']}")
            print(f"Pass Rate: {summary['pass_rate']:.1%}")
            print(f"Average Score: {summary['average_score']:.2f}")
            print()
            print("Dimension Pass Rates:")
            for dim, rate in summary.get('dimension_pass_rates', {}).items():
                print(f"  {dim}: {rate:.1%}")

        return 0 if summary and summary['pass_rate'] >= 0.8 else 1

    except Exception as e:
        print(f"Error: {e}")
        return 1


def list_benchmark_runs(
    course: Optional[str] = None,
    limit: int = 20,
) -> int:
    """List recent benchmark runs."""
    from .core.orchestrator import BenchmarkOrchestrator

    orchestrator = BenchmarkOrchestrator(endpoint_url="")

    try:
        runs = orchestrator.list_runs(course=course, limit=limit)

        if not runs:
            print("No benchmark runs found.")
            return 0

        print(f"{'Run ID':<40} {'Course':<8} {'Status':<12} {'Pass Rate':<10} {'Started'}")
        print("-" * 100)

        for run in runs:
            run_id = run.get('run_id', '')[:36]
            course = run.get('course', 'N/A')
            status = run.get('status', 'unknown')
            evaluated = run.get('evaluated_count', 0)
            passed = run.get('pass_count', 0)
            pass_rate = f"{passed/evaluated:.0%}" if evaluated else "N/A"
            started = run.get('started_at', '')
            if hasattr(started, 'strftime'):
                started = started.strftime('%Y-%m-%d %H:%M')

            print(f"{run_id:<40} {course:<8} {status:<12} {pass_rate:<10} {started}")

        return 0

    except Exception as e:
        print(f"Error: {e}")
        return 1


def run_pipeline(
    endpoint_url: str,
    num_standards: int = 40,
    course: str = "APUSH",
    verbose: bool = True,
) -> int:
    """
    Run pipeline benchmark with random standards.

    Returns exit code (0 = success, 1 = failure).
    """
    from .core.pipeline import run_pipeline_sync

    try:
        run_id = run_pipeline_sync(
            endpoint_url=endpoint_url,
            num_standards=num_standards,
            course=course,
            verbose=verbose,
        )
        return 0
    except Exception as e:
        print(f"Error: {e}")
        return 1


def show_run_details(
    run_id: str,
    output_format: str = "summary",
    failed_only: bool = False,
) -> int:
    """Show details of a benchmark run."""
    from .core.orchestrator import BenchmarkOrchestrator

    orchestrator = BenchmarkOrchestrator(endpoint_url="")

    try:
        summary = orchestrator.get_run_summary(run_id)

        if not summary:
            print(f"Run not found: {run_id}")
            return 1

        if output_format == "json":
            print(json.dumps(summary, indent=2, default=str))
        else:
            print("=" * 50)
            print(f"Benchmark Run: {run_id}")
            print("=" * 50)
            print(f"Endpoint: {summary['endpoint_url']}")
            print(f"Course: {summary['course']}")
            print(f"Status: {summary['status']}")
            print(f"Started: {summary['started_at']}")
            print(f"Completed: {summary['completed_at']}")
            print()
            print(f"Total Requests: {summary['total_requests']}")
            print(f"Successful: {summary['successful_requests']}")
            print(f"Failed Requests: {summary['failed_requests']}")
            print()
            print(f"Evaluated: {summary['evaluated_count']}")
            print(f"Passed: {summary['pass_count']}")
            print(f"Failed Evaluations: {summary['fail_count']}")
            print(f"Pass Rate: {summary['pass_rate']:.1%}")
            print(f"Average Score: {summary['average_score']:.2f}")
            print()
            print("Dimension Pass Rates:")
            for dim, rate in summary.get('dimension_pass_rates', {}).items():
                print(f"  {dim}: {rate:.1%}")

            # Show failed results if requested
            if failed_only:
                print()
                print("Failed Evaluations:")
                print("-" * 50)
                results = orchestrator.get_run_results(run_id, failed_only=True)
                for r in results[:10]:  # Limit to 10
                    print(f"\nRequest: {r.get('request_id', '')[:20]}...")
                    print(f"  Score: {r.get('overall_score', 0):.2f}")
                    print(f"  Issues: {len(r.get('issues', []))}")
                    dims = r.get('dimensions', {})
                    failed_dims = [d for d, v in dims.items() if v.get('score', 1) == 0]
                    if failed_dims:
                        print(f"  Failed Dimensions: {', '.join(failed_dims)}")

        return 0

    except Exception as e:
        print(f"Error: {e}")
        return 1


def main():
    """CLI entry point."""
    parser = argparse.ArgumentParser(
        description="AP Benchmark - Independent Question Evaluator",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s --input questions.json
  %(prog)s --calibrate
  %(prog)s --endpoint http://192.168.1.10:8000/generate --course APUSH
  %(prog)s --pipeline http://192.168.1.10:8000/generate --standards 40
  %(prog)s --list-runs
  %(prog)s --run-id <run_id> --failed-only
        """
    )

    # File-based evaluation
    parser.add_argument(
        "--input", "-i",
        help="Input JSON file containing questions"
    )

    parser.add_argument(
        "--output", "-o",
        help="Output file path (defaults to stdout)"
    )

    parser.add_argument(
        "--format", "-f",
        choices=["json", "markdown", "md", "csv", "summary"],
        default="json",
        help="Output format (default: json)"
    )

    # Endpoint benchmarking
    parser.add_argument(
        "--endpoint", "-e",
        help="Generation endpoint URL to benchmark"
    )

    parser.add_argument(
        "--course", "-c",
        default="APUSH",
        choices=["APUSH", "APWH"],
        help="Course to benchmark (default: APUSH)"
    )

    parser.add_argument(
        "--units", "-u",
        help="Comma-separated list of units (e.g., 1,2,3). Default: all"
    )

    parser.add_argument(
        "--questions", "-q",
        type=int,
        default=10,
        help="Questions per unit (default: 10)"
    )

    parser.add_argument(
        "--concurrency",
        type=int,
        default=5,
        help="Max concurrent requests (default: 5)"
    )

    # Pipeline benchmarking
    parser.add_argument(
        "--pipeline", "-p",
        metavar="URL",
        help="Run pipeline benchmark (40 random standards, all difficulties, random formats)"
    )

    parser.add_argument(
        "--standards", "-s",
        type=int,
        default=40,
        help="Number of random standards for pipeline (default: 40)"
    )

    # Run management
    parser.add_argument(
        "--list-runs",
        action="store_true",
        help="List recent benchmark runs"
    )

    parser.add_argument(
        "--run-id",
        help="Show details of a specific benchmark run"
    )

    parser.add_argument(
        "--failed-only",
        action="store_true",
        help="Show only failed evaluations (with --run-id)"
    )

    # Calibration
    parser.add_argument(
        "--calibrate",
        action="store_true",
        help="Run calibration check against gold standard"
    )

    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Enable verbose output"
    )

    parser.add_argument(
        "--version",
        action="version",
        version=f"AP Benchmark {__version__} (prompt: {__prompt_version__})"
    )

    args = parser.parse_args()

    # Parse units if provided
    units = None
    if args.units:
        units = [int(u.strip()) for u in args.units.split(",")]

    # Route to appropriate command
    if args.calibrate:
        sys.exit(run_calibration(verbose=True))

    elif args.pipeline:
        sys.exit(run_pipeline(
            endpoint_url=args.pipeline,
            num_standards=args.standards,
            course=args.course,
            verbose=True,
        ))

    elif args.endpoint:
        sys.exit(run_endpoint_benchmark(
            endpoint_url=args.endpoint,
            course=args.course,
            units=units,
            questions_per_unit=args.questions,
            concurrency=args.concurrency,
            verbose=args.verbose or True,
        ))

    elif args.list_runs:
        sys.exit(list_benchmark_runs(
            course=args.course if args.course != "APUSH" else None,
            limit=20,
        ))

    elif args.run_id:
        sys.exit(show_run_details(
            run_id=args.run_id,
            output_format=args.format,
            failed_only=args.failed_only,
        ))

    elif args.input:
        sys.exit(run_benchmark(
            input_path=args.input,
            output_format=args.format,
            output_path=args.output,
            verbose=args.verbose,
        ))

    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
