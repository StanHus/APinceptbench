# AP Question Benchmark

Evaluates AP History questions against official College Board rubrics using Claude.

## Setup

```bash
pip install -e .
export MONGODB_URI='mongodb+srv://...'
export ANTHROPIC_API_KEY='sk-ant-...'
```

## Usage

```bash
# Run benchmark (200 standards × 5 questions)
python benchmark_official.py

# Generate report from latest run
python generate_evaluation_report.py
```

## Question Types

| Type | Description | Pass Rate* |
|------|-------------|------------|
| `leq` | Long Essay | 100% |
| `dbq` | Document-Based (7 docs) | 97% |
| `saq` | Short Answer (3 parts) | 92% |
| `mcq_set` | Stimulus + 2-3 MCQs | 67% |
| `mcq` | Single MCQ | 61% |

*From 947-question benchmark run

## Evaluation

Questions pass if:
1. No critical dimension failures (factual accuracy, answer validity, document count)
2. Overall score >= 0.70

Critical dimensions vary by type. See [docs/](docs/) for details.

## Project Structure

```
benchmark_official.py      # Main benchmark runner
generate_evaluation_report.py  # Report generator
docs/
  GENERATOR_INPUTS.md      # API input reference
  reports/                 # Versioned benchmark reports
ap_benchmark/              # Core evaluation library
```

## Links

- [AP Exam Format](https://apstudents.collegeboard.org/courses/ap-united-states-history/assessment)
- [AP Rubrics](https://apcentral.collegeboard.org/courses/ap-united-states-history/exam)
