# AP Question Evaluator - Documentation Index

> **Grade Level:** AP (Advanced Placement)
> **Subjects:** APUSH, APWH
> **Purpose:** Evaluate AI-generated AP History questions against College Board rubrics

---

## ⚠️ Integration Notice

**This is a temporary standalone repo.** It will be merged into the monolithic evaluator codebase.

**Integration Team Instructions:**
1. **Read [SYSTEM_ARCHITECTURE.md](./SYSTEM_ARCHITECTURE.md)** - contains full integration requirements
2. Clone this repo temporarily
3. Copy code into monolith architecture
4. Preserve MongoDB integration initially, but make it swappable
5. Create PR against monolith
6. **Delete this cloned repo** after merge - do not maintain as separate dependency

---

## Quick Start

```bash
# 1. Install dependencies
pip install anthropic flask flask-cors pymongo python-dotenv

# 2. Set environment variables
export MONGODB_URI="mongodb+srv://..."
export ANTHROPIC_API_KEY="sk-ant-..."

# 3. Run the evaluation server
python evaluation_server.py

# 4. Test
curl http://localhost:8080/health
```

---

## Documentation Priority

### 1. Integration (Start Here)

| Document | Description |
|----------|-------------|
| **[SYSTEM_ARCHITECTURE.md](./SYSTEM_ARCHITECTURE.md)** | Complete system overview, data schemas, integration guide |
| **[EVALUATION_API.md](./EVALUATION_API.md)** | API endpoints, request/response formats |

### 2. Evaluation Logic

| Document | Description |
|----------|-------------|
| **[EVALUATION_PROCESS.md](./EVALUATION_PROCESS.md)** | How evaluation works, scoring, pass/fail criteria |
| **[AP_QUESTION_TYPES_SPEC.md](./AP_QUESTION_TYPES_SPEC.md)** | MCQ, MCQ_SET, SAQ, LEQ, DBQ specifications |

### 3. Data & Curriculum

| Document | Description |
|----------|-------------|
| **[CURRICULUM_STANDARDS.md](./CURRICULUM_STANDARDS.md)** | Curriculum structure and standards |
| **[../data/curriculum_facts.json](../data/curriculum_facts.json)** | Raw curriculum data (3,347 facts) |
| **[../data/curriculum_relationships.json](../data/curriculum_relationships.json)** | Relationships between curriculum nodes |

### 4. Generator Interface

| Document | Description |
|----------|-------------|
| **[GENERATOR_API_SPEC.md](./GENERATOR_API_SPEC.md)** | What generators should output |
| **[GENERATOR_INPUTS.md](./GENERATOR_INPUTS.md)** | What generators receive as input |

---

## Key Files

```
evaluator/
├── evaluation_server.py      # [MAIN] API server - run this
├── .env                      # Environment variables (create this)
│
├── ap_benchmark/prompts/
│   ├── official_ap_prompts.py      # [CORE] Evaluation rubric prompts
│   └── official_ap_formatters.py   # [CORE] Question formatters
│
├── data/
│   ├── curriculum_facts.json       # [DATA] All curriculum standards
│   └── curriculum_relationships.json
│
└── docs/
    ├── README.md                   # This file
    ├── SYSTEM_ARCHITECTURE.md      # [START HERE]
    └── EVALUATION_API.md           # API reference
```

---

## Integration Checklist

- [ ] Read `SYSTEM_ARCHITECTURE.md`
- [ ] Set up MongoDB access or use exported JSON (`data/curriculum_facts.json`)
- [ ] Set up Anthropic API key
- [ ] Copy `ap_benchmark/prompts/` directory (contains evaluation logic)
- [ ] Either run `evaluation_server.py` or import evaluation functions directly
- [ ] Test with sample questions

---

## Curriculum Data Summary

| Course | Facts | Units |
|--------|-------|-------|
| APUSH | 1,757 | 1-9 |
| APWH | 1,590 | 1-9 |
| **Total** | **3,347** | |

---

## Question Types Supported

| Type | Description | Hard-Fail Dimensions |
|------|-------------|---------------------|
| MCQ | Single multiple choice | `factual_accuracy`, `answer_validity` |
| MCQ_SET | 3-4 MCQs on one stimulus | `factual_accuracy`, `answer_validity` |
| SAQ | Short answer (3 parts) | `factual_accuracy`, `prompt_structure` |
| LEQ | Long essay question | `factual_accuracy`, `prompt_structure` |
| DBQ | Document-based question | `factual_accuracy`, `document_count`, `prompt_structure` |

---

## Pass/Fail Criteria

```
PASS = (no hard-fail dimension < 1.0) AND (overall_score >= 0.70)
```

---

## API Quick Reference

```bash
# Get a curriculum standard
GET /get_standard?course=APUSH

# Evaluate a question
POST /evaluate
{
  "type": "mcq",
  "difficulty": "medium",
  "request": { /* from /get_standard */ },
  "output": { /* generated question */ }
}

# Health check
GET /health
```

---

## Support

- Server logs: Check stdout or `/tmp/eval_server.log`
- Benchmark reports: `docs/reports/`
- Test suite: `python test_server.py`
