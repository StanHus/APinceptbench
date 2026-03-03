#!/usr/bin/env python3
"""
Comprehensive Detailed Evaluation Report Generator

Generates detailed reports with ACTUAL question content examples,
showing exactly what the generator produced and why it failed/passed.
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
    """Get the most recent benchmark run."""
    db = get_db()
    runs = list(db.benchmark_runs.find().sort("started_at", -1).limit(5))
    for run in runs:
        if run.get("passed", 0) > 0 or run.get("failed", 0) > 0:
            return run
    return runs[0] if runs else None


def format_mcq_content(question_data: dict) -> str:
    """Format MCQ question content for display."""
    output = question_data.get("output", question_data)
    lines = []

    if output.get("stimulus"):
        lines.append(f"**Stimulus:**\n> {output['stimulus'][:500]}...")
        lines.append("")

    lines.append(f"**Stem:** {output.get('stem', 'N/A')}")
    lines.append("")

    # Handle different answer formats
    choices = output.get("choices") or output.get("answer_options") or output.get("options")
    if isinstance(choices, dict):
        lines.append("**Choices:**")
        for key in ["A", "B", "C", "D"]:
            if key in choices:
                lines.append(f"- **{key}:** {choices[key][:200]}")
    elif isinstance(choices, list):
        lines.append("**Choices:**")
        for opt in choices[:4]:
            if isinstance(opt, dict):
                lines.append(f"- **{opt.get('key', '?')}:** {opt.get('text', str(opt))[:200]}")
            else:
                lines.append(f"- {str(opt)[:200]}")
    else:
        lines.append("**Choices:** *Not found or malformed*")

    lines.append("")
    lines.append(f"**Correct Answer:** {output.get('correct_answer', 'N/A')}")

    if output.get("explanation"):
        lines.append(f"\n**Explanation:** {output['explanation'][:300]}...")

    return "\n".join(lines)


def format_mcq_set_content(question_data: dict) -> str:
    """Format MCQ_SET question content for display."""
    output = question_data.get("output", question_data)
    lines = []

    if output.get("stimulus"):
        lines.append(f"**Shared Stimulus:**\n> {output['stimulus'][:600]}...")
        lines.append("")

    questions = output.get("questions", [])
    for i, q in enumerate(questions[:3], 1):
        lines.append(f"### Question {i}")
        lines.append(f"**Stem:** {q.get('stem', 'N/A')}")

        choices = q.get("choices") or q.get("answer_options") or q.get("options")
        if isinstance(choices, dict):
            for key in ["A", "B", "C", "D"]:
                if key in choices:
                    lines.append(f"- **{key}:** {choices[key][:150]}")

        lines.append(f"**Correct:** {q.get('correct_answer', 'N/A')}")
        lines.append("")

    return "\n".join(lines)


def format_saq_content(question_data: dict) -> str:
    """Format SAQ question content for display."""
    output = question_data.get("output", question_data)
    lines = []

    if output.get("stimulus"):
        lines.append(f"**Stimulus:**\n> {output['stimulus'][:400]}...")
        lines.append("")

    if output.get("preamble"):
        lines.append(f"**Preamble:** {output['preamble']}")
        lines.append("")

    parts = output.get("parts", {})
    for part_key in ["a", "b", "c"]:
        part = parts.get(part_key, {})
        if isinstance(part, dict):
            lines.append(f"**Part ({part_key}):** {part.get('prompt', 'N/A')}")
            if part.get("skill"):
                lines.append(f"  - *Skill:* {part['skill']}")
            if part.get("scoring_notes"):
                lines.append(f"  - *Scoring:* {part['scoring_notes'][:100]}...")
        else:
            lines.append(f"**Part ({part_key}):** {str(part)[:200]}")
        lines.append("")

    return "\n".join(lines)


def format_leq_content(question_data: dict) -> str:
    """Format LEQ question content for display."""
    output = question_data.get("output", question_data)
    lines = []

    lines.append(f"**Prompt:**\n> {output.get('prompt', 'N/A')}")
    lines.append("")
    lines.append(f"**Reasoning Type:** {output.get('reasoning_type', 'N/A')}")
    lines.append(f"**Time Period:** {output.get('time_period_explicit', 'N/A')}")

    guidance = output.get("scoring_guidance", {})
    if guidance:
        lines.append("")
        lines.append("**Scoring Guidance:**")
        if guidance.get("thesis_examples"):
            lines.append(f"- Thesis Examples: {guidance['thesis_examples'][0][:150]}...")
        if guidance.get("evidence_expectations"):
            lines.append(f"- Evidence: {guidance['evidence_expectations'][:150]}...")

    return "\n".join(lines)


def format_dbq_content(question_data: dict) -> str:
    """Format DBQ question content for display."""
    output = question_data.get("output", question_data)
    lines = []

    lines.append(f"**Prompt:**\n> {output.get('prompt', 'N/A')}")
    lines.append("")

    docs = output.get("documents", [])
    lines.append(f"**Documents ({len(docs)} total):**")
    lines.append("")

    for doc in docs[:3]:  # Show first 3 documents
        lines.append(f"**Document {doc.get('number', '?')}:**")
        lines.append(f"- *Source:* {doc.get('source', 'N/A')}")
        lines.append(f"- *Type:* {doc.get('type', 'N/A')}")
        content = doc.get('content', '')
        lines.append(f"- *Content:* {content[:200]}..." if len(content) > 200 else f"- *Content:* {content}")
        lines.append("")

    if len(docs) > 3:
        lines.append(f"*... and {len(docs) - 3} more documents*")

    return "\n".join(lines)


def format_question_content(question_data: dict, qtype: str) -> str:
    """Format question content based on type."""
    formatters = {
        "mcq": format_mcq_content,
        "mcq_set": format_mcq_set_content,
        "saq": format_saq_content,
        "leq": format_leq_content,
        "dbq": format_dbq_content,
    }
    formatter = formatters.get(qtype, lambda x: json.dumps(x, indent=2, default=str)[:1000])
    try:
        return formatter(question_data)
    except Exception as e:
        return f"*Error formatting: {e}*\n\nRaw: {json.dumps(question_data, indent=2, default=str)[:500]}"


def format_dimension_details(dimensions: dict) -> str:
    """Format dimension scores with details."""
    lines = []
    for dim_name, dim_data in sorted(dimensions.items()):
        if isinstance(dim_data, dict):
            score = dim_data.get("score", 0)
            notes = dim_data.get("notes", "")
            status = "✓" if score >= 1.0 else "✗" if score < 0.5 else "◐"
            line = f"| {status} {dim_name} | {score:.2f} |"
            if notes:
                line += f" {notes[:60]}... |"
            lines.append(line)
        else:
            score = float(dim_data) if dim_data else 0
            status = "✓" if score >= 1.0 else "✗" if score < 0.5 else "◐"
            lines.append(f"| {status} {dim_name} | {score:.2f} |")
    return "\n".join(lines)


def generate_comprehensive_report(run_id: str = None) -> str:
    """Generate a comprehensive report with actual question examples."""
    db = get_db()

    if not run_id:
        run = get_latest_run()
        if not run:
            return "No benchmark runs found!"
        run_id = run["_id"]

    # Get run info
    run = db.benchmark_runs.find_one({"_id": run_id})

    # Get all evaluations and questions
    evaluations = list(db.benchmark_evaluations.find({"run_id": run_id}))
    questions = list(db.benchmark_questions.find({"run_id": run_id}))
    q_lookup = {q["_id"]: q for q in questions}

    # Build analysis
    by_type = defaultdict(lambda: {"passed": [], "failed": [], "errors": []})
    dimension_stats = defaultdict(lambda: {"scores": [], "failures": []})
    critical_failures = []

    for ev in evaluations:
        qid = ev.get("question_id")
        q = q_lookup.get(qid, {})
        qtype = ev.get("type", "unknown")

        entry = {
            "evaluation": ev,
            "question": q,
            "score": ev.get("overall_score", 0),
            "dimensions": ev.get("dimensions", {}),
            "issues": ev.get("issues", []),
        }

        if ev.get("evaluation_success") == False:
            by_type[qtype]["errors"].append(entry)
        elif ev.get("passed"):
            by_type[qtype]["passed"].append(entry)
        else:
            by_type[qtype]["failed"].append(entry)

            # Track critical failures
            if ev.get("critical_failed"):
                critical_failures.append(entry)

        # Track dimension stats
        for dim_name, dim_data in ev.get("dimensions", {}).items():
            score = dim_data.get("score", dim_data) if isinstance(dim_data, dict) else dim_data
            dimension_stats[dim_name]["scores"].append(score)
            if score < 1.0:
                dimension_stats[dim_name]["failures"].append({
                    "type": qtype,
                    "score": score,
                    "notes": dim_data.get("notes", "") if isinstance(dim_data, dict) else "",
                })

    # Generate report
    lines = []
    lines.append("# Comprehensive AP Question Evaluation Report (Detailed)")
    lines.append("")
    lines.append(f"**Run ID:** `{run_id}`")
    lines.append(f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    if run:
        lines.append(f"**Endpoint:** `{run.get('endpoint', 'N/A')}`")
        lines.append(f"**Standards Sampled:** {run.get('standards_sampled', 'N/A')}")
    lines.append("")

    # Executive Summary
    total_passed = sum(len(t["passed"]) for t in by_type.values())
    total_failed = sum(len(t["failed"]) for t in by_type.values())
    total_errors = sum(len(t["errors"]) for t in by_type.values())
    total = total_passed + total_failed + total_errors
    pass_rate = (total_passed / total * 100) if total > 0 else 0

    lines.append("## Executive Summary")
    lines.append("")
    lines.append(f"| Metric | Value |")
    lines.append(f"|--------|-------|")
    lines.append(f"| Total Questions | {total} |")
    lines.append(f"| **Passed** | **{total_passed} ({pass_rate:.1f}%)** |")
    lines.append(f"| Failed | {total_failed} |")
    lines.append(f"| Evaluation Errors | {total_errors} |")
    lines.append("")

    # By Type Summary
    lines.append("## Performance by Question Type")
    lines.append("")
    lines.append("| Type | Passed | Failed | Errors | Pass Rate |")
    lines.append("|------|--------|--------|--------|-----------|")

    for qtype in ["mcq", "mcq_set", "saq", "leq", "dbq"]:
        data = by_type[qtype]
        p, f, e = len(data["passed"]), len(data["failed"]), len(data["errors"])
        total_type = p + f
        rate = (p / total_type * 100) if total_type > 0 else 0
        lines.append(f"| {qtype.upper()} | {p} | {f} | {e} | {rate:.1f}% |")
    lines.append("")

    # Dimension Analysis
    lines.append("## Dimension Performance (Sorted by Pass Rate)")
    lines.append("")
    lines.append("| Dimension | Avg Score | Pass Rate | Total |")
    lines.append("|-----------|-----------|-----------|-------|")

    dim_summary = []
    for dim_name, stats in dimension_stats.items():
        scores = stats["scores"]
        if scores:
            avg = sum(scores) / len(scores)
            pass_count = sum(1 for s in scores if s >= 1.0)
            pass_rate = pass_count / len(scores) * 100
            dim_summary.append((dim_name, avg, pass_rate, len(scores)))

    for dim_name, avg, rate, total in sorted(dim_summary, key=lambda x: x[2]):
        status = "🔴" if rate < 30 else "🟡" if rate < 70 else "🟢"
        lines.append(f"| {status} {dim_name} | {avg:.2f} | {rate:.1f}% | {total} |")
    lines.append("")

    # ============================================
    # DETAILED EXAMPLES SECTION
    # ============================================

    lines.append("---")
    lines.append("# Detailed Question Examples")
    lines.append("")
    lines.append("This section shows **actual question content** with evaluation details.")
    lines.append("")

    # Show examples for each type
    for qtype in ["mcq", "mcq_set", "saq", "leq", "dbq"]:
        data = by_type[qtype]

        lines.append(f"## {qtype.upper()} Questions")
        lines.append("")

        # Show 2 failures first (more important)
        if data["failed"]:
            lines.append(f"### ❌ {qtype.upper()} Failures ({len(data['failed'])} total)")
            lines.append("")

            for i, entry in enumerate(sorted(data["failed"], key=lambda x: x["score"])[:2], 1):
                q = entry["question"]
                ev = entry["evaluation"]

                lines.append(f"#### Failure #{i}: Score {entry['score']:.2f}")
                lines.append("")
                lines.append(f"**Curriculum Context:**")
                lines.append(f"- Course: {q.get('course', 'N/A')}")
                lines.append(f"- Unit: {q.get('unit', 'N/A')}")
                lines.append(f"- Topic: {q.get('topic', 'N/A')}")
                lines.append(f"- Difficulty: {q.get('difficulty', 'N/A')}")
                lines.append("")

                lines.append("**Generated Question Content:**")
                lines.append("")
                lines.append("```")
                question_data = q.get("question_data", {})
                lines.append(format_question_content(question_data, qtype))
                lines.append("```")
                lines.append("")

                lines.append("**Evaluation Dimensions:**")
                lines.append("")
                lines.append("| Status | Dimension | Score |")
                lines.append("|--------|-----------|-------|")
                for dim_name, dim_data in sorted(entry["dimensions"].items()):
                    score = dim_data.get("score", dim_data) if isinstance(dim_data, dict) else dim_data
                    status = "✓" if score >= 1.0 else "✗" if score < 0.7 else "◐"
                    lines.append(f"| {status} | {dim_name} | {score:.2f} |")
                lines.append("")

                if entry["issues"]:
                    lines.append("**Issues Identified:**")
                    for issue in entry["issues"][:5]:
                        if isinstance(issue, dict):
                            lines.append(f"- **{issue.get('dimension', 'N/A')}** ({issue.get('severity', 'N/A')}): {issue.get('description', str(issue))[:300]}")
                        else:
                            lines.append(f"- {str(issue)[:300]}")
                    lines.append("")

                lines.append("---")
                lines.append("")

        # Show 1 passing example
        if data["passed"]:
            lines.append(f"### ✅ {qtype.upper()} Passing Example")
            lines.append("")

            entry = max(data["passed"], key=lambda x: x["score"])
            q = entry["question"]

            lines.append(f"**Score:** {entry['score']:.2f}")
            lines.append("")
            lines.append(f"**Curriculum Context:**")
            lines.append(f"- Course: {q.get('course', 'N/A')}")
            lines.append(f"- Topic: {q.get('topic', 'N/A')}")
            lines.append("")

            lines.append("**Generated Question Content:**")
            lines.append("")
            lines.append("```")
            question_data = q.get("question_data", {})
            lines.append(format_question_content(question_data, qtype))
            lines.append("```")
            lines.append("")

        lines.append("")

    # Critical Failures Analysis
    if critical_failures:
        lines.append("---")
        lines.append("# Critical Failures Analysis")
        lines.append("")
        lines.append("These questions failed due to **hard fail** dimensions (structural requirements that MUST pass):")
        lines.append("")

        for i, entry in enumerate(critical_failures[:5], 1):
            q = entry["question"]
            lines.append(f"### Critical Failure #{i}: {entry['evaluation'].get('type', 'N/A').upper()}")
            lines.append("")
            lines.append(f"**Topic:** {q.get('topic', 'N/A')}")
            lines.append(f"**Score:** {entry['score']:.2f}")
            lines.append("")

            # Show which hard-fail dimension failed
            hard_fail_dims = ["document_count", "prompt_structure", "factual_accuracy", "answer_validity"]
            for dim in hard_fail_dims:
                if dim in entry["dimensions"]:
                    dim_data = entry["dimensions"][dim]
                    score = dim_data.get("score", dim_data) if isinstance(dim_data, dict) else dim_data
                    if score < 1.0:
                        notes = dim_data.get("notes", "") if isinstance(dim_data, dict) else ""
                        lines.append(f"**HARD FAIL: `{dim}` = {score:.2f}**")
                        if notes:
                            lines.append(f"> {notes}")
                        lines.append("")

            lines.append("")

    # Recommendations
    lines.append("---")
    lines.append("# Recommendations")
    lines.append("")

    # Analyze worst dimensions
    worst_dims = sorted(dim_summary, key=lambda x: x[2])[:5]

    if worst_dims:
        lines.append("## Priority Improvements (Worst Performing Dimensions)")
        lines.append("")
        for dim_name, avg, rate, total in worst_dims:
            lines.append(f"### 🔴 `{dim_name}` - {rate:.1f}% pass rate")
            lines.append("")

            # Get example failures
            failures = dimension_stats[dim_name]["failures"][:3]
            if failures:
                lines.append("**Example failures:**")
                for f in failures:
                    lines.append(f"- {f['type'].upper()}: score={f['score']:.2f} - {f['notes'][:100] if f['notes'] else 'No notes'}")
                lines.append("")

    # Type-specific recommendations
    for qtype in ["mcq", "mcq_set", "saq", "leq", "dbq"]:
        data = by_type[qtype]
        p, f = len(data["passed"]), len(data["failed"])
        if p + f > 0:
            rate = p / (p + f) * 100
            if rate < 60:
                lines.append(f"## {qtype.upper()} Specific Issues ({rate:.1f}% pass rate)")
                lines.append("")

                # Aggregate issues
                issue_counts = defaultdict(int)
                for entry in data["failed"]:
                    for issue in entry["issues"]:
                        if isinstance(issue, dict):
                            key = f"{issue.get('dimension', 'unknown')}: {issue.get('description', '')[:80]}"
                        else:
                            key = str(issue)[:80]
                        issue_counts[key] += 1

                lines.append("**Common issues:**")
                for issue, count in sorted(issue_counts.items(), key=lambda x: -x[1])[:5]:
                    lines.append(f"- ({count}x) {issue}")
                lines.append("")

    lines.append("")
    lines.append("---")
    lines.append("*Generated by AP Benchmark Detailed Report Generator*")

    return "\n".join(lines)


def main():
    import sys

    run_id = sys.argv[1] if len(sys.argv) > 1 else None
    report = generate_comprehensive_report(run_id)

    # Save report
    reports_dir = os.path.join(os.path.dirname(__file__), "docs", "reports")
    os.makedirs(reports_dir, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"detailed_report_{timestamp}.md"
    filepath = os.path.join(reports_dir, filename)

    with open(filepath, "w") as f:
        f.write(report)

    print(f"Report saved to: {filepath}")
    print(report)


if __name__ == "__main__":
    main()
