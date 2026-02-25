#!/usr/bin/env python3
"""
Comprehensive Evaluation Report Generator

Analyzes benchmark runs and generates detailed reports on question quality,
failure patterns, and improvement recommendations.
"""

import json
import os
from collections import defaultdict
from datetime import datetime
from pymongo import MongoClient

# Configuration
MONGODB_URI = os.environ.get('MONGODB_URI')
if not MONGODB_URI:
    raise ValueError("MONGODB_URI environment variable is required")
DB_NAME = "ap_social_studies"

def get_db():
    client = MongoClient(MONGODB_URI, serverSelectionTimeoutMS=10000)
    return client[DB_NAME]

def get_latest_run():
    """Get the most recent benchmark run with results."""
    db = get_db()
    runs = list(db.benchmark_runs.find().sort("started_at", -1).limit(5))
    # Find one with actual passes
    for run in runs:
        if run.get("passed", 0) > 0:
            return run
    return runs[0] if runs else None

def analyze_run(run_id: str):
    """Perform comprehensive analysis of a benchmark run."""
    db = get_db()

    # Get all evaluations for this run
    evaluations = list(db.benchmark_evaluations.find({"run_id": run_id}))
    questions = list(db.benchmark_questions.find({"run_id": run_id}))

    # Build question lookup
    q_lookup = {q["_id"]: q for q in questions}

    # Analysis structures
    analysis = {
        "run_id": run_id,
        "total_evaluated": len(evaluations),
        "passed": 0,
        "failed": 0,
        "errors": 0,
        "by_type": defaultdict(lambda: {"passed": 0, "failed": 0, "errors": 0, "scores": [], "issues": []}),
        "by_course": defaultdict(lambda: {"passed": 0, "failed": 0, "scores": []}),
        "by_dimension": defaultdict(lambda: {"pass": 0, "fail": 0, "scores": []}),
        "critical_failures": defaultdict(int),
        "common_issues": defaultdict(int),
        "score_distribution": {"0-0.2": 0, "0.2-0.4": 0, "0.4-0.6": 0, "0.6-0.8": 0, "0.8-1.0": 0},
        "detailed_failures": [],
        "detailed_passes": [],
    }

    for ev in evaluations:
        qid = ev.get("question_id")
        q = q_lookup.get(qid, {})
        qtype = ev.get("type", "unknown")
        course = q.get("course", "unknown")

        if ev.get("evaluation_success") == False:
            analysis["errors"] += 1
            analysis["by_type"][qtype]["errors"] += 1
            continue

        passed = ev.get("passed", False)
        score = ev.get("overall_score", 0) or 0

        # Overall counts
        if passed:
            analysis["passed"] += 1
            analysis["by_type"][qtype]["passed"] += 1
            analysis["by_course"][course]["passed"] += 1
        else:
            analysis["failed"] += 1
            analysis["by_type"][qtype]["failed"] += 1
            analysis["by_course"][course]["failed"] += 1

        # Score tracking
        analysis["by_type"][qtype]["scores"].append(score)
        analysis["by_course"][course]["scores"].append(score)

        # Score distribution
        if score < 0.2:
            analysis["score_distribution"]["0-0.2"] += 1
        elif score < 0.4:
            analysis["score_distribution"]["0.2-0.4"] += 1
        elif score < 0.6:
            analysis["score_distribution"]["0.4-0.6"] += 1
        elif score < 0.8:
            analysis["score_distribution"]["0.6-0.8"] += 1
        else:
            analysis["score_distribution"]["0.8-1.0"] += 1

        # Dimension analysis
        dimensions = ev.get("dimensions", {})
        for dim_name, dim_data in dimensions.items():
            if isinstance(dim_data, dict):
                dim_score = dim_data.get("score", 0)
            else:
                dim_score = float(dim_data) if dim_data else 0

            analysis["by_dimension"][dim_name]["scores"].append(dim_score)
            if dim_score >= 1.0:
                analysis["by_dimension"][dim_name]["pass"] += 1
            else:
                analysis["by_dimension"][dim_name]["fail"] += 1

        # Critical failure tracking
        if ev.get("critical_failed"):
            for dim_name in ["document_count", "prompt_structure", "factual_accuracy", "answer_validity"]:
                if dim_name in dimensions:
                    dim_data = dimensions[dim_name]
                    dim_score = dim_data.get("score", 1.0) if isinstance(dim_data, dict) else dim_data
                    if dim_score < 1.0:
                        analysis["critical_failures"][f"{qtype}:{dim_name}"] += 1

        # Issue tracking
        issues = ev.get("issues", [])
        for issue in issues:
            if isinstance(issue, str):
                # Truncate long issues
                short_issue = issue[:100] + "..." if len(issue) > 100 else issue
                analysis["common_issues"][short_issue] += 1
                analysis["by_type"][qtype]["issues"].append(issue)

        # Detailed tracking for report
        detail = {
            "type": qtype,
            "course": course,
            "score": score,
            "topic": q.get("topic", ""),
            "dimensions": dimensions,
            "issues": issues,
        }

        if passed:
            analysis["detailed_passes"].append(detail)
        else:
            analysis["detailed_failures"].append(detail)

    return analysis

def generate_markdown_report(analysis: dict) -> str:
    """Generate comprehensive markdown report."""

    lines = []
    lines.append("# Comprehensive AP Question Evaluation Report")
    lines.append("")
    lines.append(f"**Run ID:** `{analysis['run_id']}`")
    lines.append(f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    lines.append(f"**Evaluator Version:** 2026.02.24.1")
    lines.append("")

    # Executive Summary
    lines.append("## Executive Summary")
    lines.append("")
    total = analysis["total_evaluated"]
    passed = analysis["passed"]
    failed = analysis["failed"]
    errors = analysis["errors"]
    rate = (passed / total * 100) if total > 0 else 0

    lines.append(f"| Metric | Value |")
    lines.append(f"|--------|-------|")
    lines.append(f"| Total Evaluated | {total} |")
    lines.append(f"| Passed | {passed} ({rate:.1f}%) |")
    lines.append(f"| Failed | {failed} |")
    lines.append(f"| Evaluation Errors | {errors} |")
    lines.append("")

    # Score Distribution
    lines.append("### Score Distribution")
    lines.append("")
    lines.append("```")
    dist = analysis["score_distribution"]
    max_count = max(dist.values()) if dist.values() else 1
    for bucket, count in sorted(dist.items()):
        bar = "█" * int(count / max_count * 30) if max_count > 0 else ""
        lines.append(f"{bucket:8} | {bar} {count}")
    lines.append("```")
    lines.append("")

    # Performance by Question Type
    lines.append("## Performance by Question Type")
    lines.append("")
    lines.append("| Type | Passed | Failed | Errors | Pass Rate | Avg Score |")
    lines.append("|------|--------|--------|--------|-----------|-----------|")

    for qtype in ["mcq", "mcq_set", "saq", "leq", "dbq"]:
        data = analysis["by_type"][qtype]
        p = data["passed"]
        f = data["failed"]
        e = data["errors"]
        total_type = p + f
        rate = (p / total_type * 100) if total_type > 0 else 0
        avg = sum(data["scores"]) / len(data["scores"]) if data["scores"] else 0
        lines.append(f"| {qtype.upper():8} | {p:6} | {f:6} | {e:6} | {rate:8.1f}% | {avg:9.2f} |")
    lines.append("")

    # Detailed Type Analysis
    lines.append("### Detailed Analysis by Type")
    lines.append("")

    for qtype in ["mcq", "mcq_set", "saq", "leq", "dbq"]:
        data = analysis["by_type"][qtype]
        p = data["passed"]
        f = data["failed"]
        total_type = p + f

        if total_type == 0:
            continue

        lines.append(f"#### {qtype.upper()}")
        lines.append("")

        # Get type-specific issues
        type_issues = data["issues"]
        if type_issues:
            issue_counts = defaultdict(int)
            for issue in type_issues:
                short = issue[:80] + "..." if len(issue) > 80 else issue
                issue_counts[short] += 1

            lines.append("**Common Issues:**")
            for issue, count in sorted(issue_counts.items(), key=lambda x: -x[1])[:5]:
                lines.append(f"- ({count}x) {issue}")
            lines.append("")

    # Performance by Course
    lines.append("## Performance by Course")
    lines.append("")
    lines.append("| Course | Passed | Failed | Pass Rate | Avg Score |")
    lines.append("|--------|--------|--------|-----------|-----------|")

    for course in ["APUSH", "APWH"]:
        data = analysis["by_course"][course]
        p = data["passed"]
        f = data["failed"]
        total_course = p + f
        rate = (p / total_course * 100) if total_course > 0 else 0
        avg = sum(data["scores"]) / len(data["scores"]) if data["scores"] else 0
        lines.append(f"| {course:6} | {p:6} | {f:6} | {rate:8.1f}% | {avg:9.2f} |")
    lines.append("")

    # Dimension Analysis
    lines.append("## Evaluation Dimensions Analysis")
    lines.append("")
    lines.append("This section shows performance across all evaluation dimensions.")
    lines.append("")
    lines.append("| Dimension | Pass | Fail | Pass Rate | Avg Score |")
    lines.append("|-----------|------|------|-----------|-----------|")

    dim_data = []
    for dim_name, data in analysis["by_dimension"].items():
        p = data["pass"]
        f = data["fail"]
        total_dim = p + f
        rate = (p / total_dim * 100) if total_dim > 0 else 0
        avg = sum(data["scores"]) / len(data["scores"]) if data["scores"] else 0
        dim_data.append((dim_name, p, f, rate, avg))

    # Sort by pass rate ascending (worst first)
    for dim_name, p, f, rate, avg in sorted(dim_data, key=lambda x: x[3]):
        lines.append(f"| {dim_name:25} | {p:4} | {f:4} | {rate:8.1f}% | {avg:9.2f} |")
    lines.append("")

    # Critical Failures
    lines.append("## Critical Failures Analysis")
    lines.append("")
    lines.append("Critical failures are structural issues that cause automatic failure regardless of score.")
    lines.append("")

    if analysis["critical_failures"]:
        lines.append("| Type:Dimension | Count |")
        lines.append("|----------------|-------|")
        for key, count in sorted(analysis["critical_failures"].items(), key=lambda x: -x[1]):
            lines.append(f"| {key} | {count} |")
    else:
        lines.append("*No critical failures detected in this run.*")
    lines.append("")

    # Common Issues
    lines.append("## Most Common Issues")
    lines.append("")

    if analysis["common_issues"]:
        lines.append("| Issue | Count |")
        lines.append("|-------|-------|")
        for issue, count in sorted(analysis["common_issues"].items(), key=lambda x: -x[1])[:15]:
            lines.append(f"| {issue} | {count} |")
    else:
        lines.append("*No common issues logged.*")
    lines.append("")

    # Sample Passing Questions
    lines.append("## Sample Passing Questions")
    lines.append("")

    passes = analysis["detailed_passes"][:5]
    if passes:
        for i, detail in enumerate(passes, 1):
            lines.append(f"### Pass #{i}: {detail['type'].upper()} ({detail['course']})")
            lines.append(f"- **Score:** {detail['score']:.2f}")
            lines.append(f"- **Topic:** {detail['topic'][:80] if detail['topic'] else 'N/A'}")

            # Show dimension scores
            dims = detail.get("dimensions", {})
            if dims:
                dim_scores = []
                for d, v in dims.items():
                    s = v.get("score", v) if isinstance(v, dict) else v
                    dim_scores.append(f"{d}={s:.1f}")
                lines.append(f"- **Dimensions:** {', '.join(dim_scores[:6])}")
            lines.append("")
    else:
        lines.append("*No passing questions in this run.*")
        lines.append("")

    # Sample Failing Questions
    lines.append("## Sample Failing Questions")
    lines.append("")

    # Get variety of failures
    failures_by_type = defaultdict(list)
    for f in analysis["detailed_failures"]:
        failures_by_type[f["type"]].append(f)

    sample_failures = []
    for qtype in ["dbq", "mcq_set", "mcq", "saq", "leq"]:
        if failures_by_type[qtype]:
            sample_failures.append(failures_by_type[qtype][0])

    for i, detail in enumerate(sample_failures[:5], 1):
        lines.append(f"### Failure #{i}: {detail['type'].upper()} ({detail['course']})")
        lines.append(f"- **Score:** {detail['score']:.2f}")
        lines.append(f"- **Topic:** {detail['topic'][:80] if detail['topic'] else 'N/A'}")

        # Show failing dimensions
        dims = detail.get("dimensions", {})
        failing_dims = []
        for d, v in dims.items():
            s = v.get("score", v) if isinstance(v, dict) else v
            if s < 1.0:
                failing_dims.append(f"{d}={s:.1f}")
        if failing_dims:
            lines.append(f"- **Failing Dimensions:** {', '.join(failing_dims[:6])}")

        # Show issues
        issues = detail.get("issues", [])
        if issues:
            lines.append(f"- **Issues:**")
            for issue in issues[:3]:
                short = issue[:100] + "..." if len(issue) > 100 else issue
                lines.append(f"  - {short}")
        lines.append("")

    # Recommendations
    lines.append("## Recommendations for Generator Improvement")
    lines.append("")

    # Analyze patterns and make recommendations
    recs = []

    # Check DBQ performance
    dbq_data = analysis["by_type"]["dbq"]
    if dbq_data["passed"] == 0 and (dbq_data["failed"] + dbq_data["errors"]) > 0:
        recs.append({
            "priority": "HIGH",
            "type": "DBQ",
            "issue": "0% pass rate",
            "recommendation": "Ensure DBQ generator produces exactly 7 primary source documents with proper attribution (author, date, source type). Each document must be historically authentic and diverse in perspective."
        })

    # Check MCQ_set performance
    mcq_set_data = analysis["by_type"]["mcq_set"]
    if mcq_set_data["passed"] == 0 and (mcq_set_data["failed"] + mcq_set_data["errors"]) > 0:
        recs.append({
            "priority": "HIGH",
            "type": "MCQ_SET",
            "issue": "0% pass rate",
            "recommendation": "MCQ sets must include a stimulus (text, image, or data) with 2-4 questions that directly reference the stimulus. Ensure each question has exactly one correct answer."
        })

    # Check MCQ performance
    mcq_data = analysis["by_type"]["mcq"]
    mcq_rate = mcq_data["passed"] / (mcq_data["passed"] + mcq_data["failed"]) if (mcq_data["passed"] + mcq_data["failed"]) > 0 else 0
    if mcq_rate < 0.5:
        recs.append({
            "priority": "MEDIUM",
            "type": "MCQ",
            "issue": f"{mcq_rate*100:.0f}% pass rate",
            "recommendation": "Review answer_validity dimension. Ensure exactly one answer is unambiguously correct. Avoid overlapping or partially correct distractors."
        })

    # Check dimension failures
    for dim_name, data in analysis["by_dimension"].items():
        total = data["pass"] + data["fail"]
        if total > 5:
            rate = data["pass"] / total
            if rate < 0.3:
                recs.append({
                    "priority": "MEDIUM",
                    "type": "ALL",
                    "issue": f"{dim_name} dimension at {rate*100:.0f}%",
                    "recommendation": f"Focus on improving {dim_name}. Review rubric requirements and ensure generator explicitly addresses this dimension."
                })

    # Output recommendations
    if recs:
        for rec in sorted(recs, key=lambda x: {"HIGH": 0, "MEDIUM": 1, "LOW": 2}.get(x["priority"], 3)):
            lines.append(f"### [{rec['priority']}] {rec['type']}: {rec['issue']}")
            lines.append("")
            lines.append(f"{rec['recommendation']}")
            lines.append("")
    else:
        lines.append("Generator is performing adequately. Continue monitoring for regression.")
        lines.append("")

    # Conclusion
    lines.append("## Conclusion")
    lines.append("")

    if rate >= 70:
        lines.append("The generator is performing well, meeting AP standards for most question types.")
    elif rate >= 40:
        lines.append("The generator shows moderate performance. Focus on the recommendations above to improve pass rates.")
    else:
        lines.append("The generator requires significant improvement. Priority should be given to structural requirements (document counts, answer validity) before addressing quality dimensions.")
    lines.append("")
    lines.append("---")
    lines.append("*Report generated by Official AP Benchmark Evaluator*")

    return "\n".join(lines)


def main():
    print("Fetching latest benchmark run...")
    run = get_latest_run()

    if not run:
        print("No benchmark runs found!")
        return

    run_id = run["_id"]
    print(f"Analyzing run: {run_id}")
    print(f"  Started: {run.get('started_at')}")
    print(f"  Pass rate: {run.get('pass_rate', 0)*100:.1f}%")

    print("\nPerforming comprehensive analysis...")
    analysis = analyze_run(run_id)

    print("Generating report...")
    report = generate_markdown_report(analysis)

    # Ensure reports directory exists
    reports_dir = os.path.join(os.path.dirname(__file__), "docs", "reports")
    os.makedirs(reports_dir, exist_ok=True)

    # Save versioned report with timestamp and run_id
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    short_run_id = run_id[:8] if len(run_id) > 8 else run_id
    report_filename = f"evaluation_{timestamp}_{short_run_id}.md"
    report_path = os.path.join(reports_dir, report_filename)

    with open(report_path, "w") as f:
        f.write(report)

    # Also save as latest for quick access
    latest_path = os.path.join(reports_dir, "LATEST.md")
    with open(latest_path, "w") as f:
        f.write(report)

    print(f"\nReport saved to: {report_path}")
    print(f"Latest symlink: {latest_path}")
    print(f"\nSummary:")
    print(f"  Total: {analysis['total_evaluated']}")
    print(f"  Passed: {analysis['passed']}")
    print(f"  Failed: {analysis['failed']}")
    print(f"  Errors: {analysis['errors']}")


if __name__ == "__main__":
    main()
