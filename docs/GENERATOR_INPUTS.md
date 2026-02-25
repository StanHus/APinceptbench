# Generator Input Reference

API endpoint: `POST /generate`

## Required

| Field | Type | Values |
|-------|------|--------|
| `type` | string | `mcq`, `mcq_set`, `saq`, `leq`, `dbq` |
| `difficulty` | string | `easy`, `medium`, `hard` |
| `course` | string | `APUSH`, `APWH` |

## Curriculum Context

| Field | Type | DB Field |
|-------|------|----------|
| `unit` | int | `unit` |
| `topic` | string | `cluster` |
| `learning_objective` | string | `learning_objective` |
| `curriculum_fact` | string | `statement` |
| `time_period` | string | `date` |
| `theme` | string | `theme` |
| `node_id` | string | `node_id` |

## LEQ Only

| Field | Values |
|-------|--------|
| `reasoning_type` | `causation`, `comparison`, `ccot` |

## Question Types

| Type | Output | Section |
|------|--------|---------|
| `mcq` | 1 question, 4 choices | I-A |
| `mcq_set` | Stimulus + 2-3 questions | I-A |
| `saq` | 3-part short answer | I-B |
| `leq` | Essay prompt | II-B |
| `dbq` | Prompt + 7 documents | II-A |

See: [AP Exam Format](https://apstudents.collegeboard.org/courses/ap-united-states-history/assessment)

## Theme Codes

**APUSH**: `NAT` `WXT` `GEO` `MIG` `PCE` `ARC` `SOC`
**APWH**: `GOV` `ECN` `SOC` `CDI` `TEC` `ENV`

See: [APUSH Themes](https://apcentral.collegeboard.org/courses/ap-united-states-history/course) | [APWH Themes](https://apcentral.collegeboard.org/courses/ap-world-history/course)

## Example

```json
{
  "type": "mcq",
  "difficulty": "medium",
  "course": "APUSH",
  "unit": 1,
  "topic": "Native American Societies Before European Contact",
  "learning_objective": "Explain how and why various native populations...",
  "curriculum_fact": "The spread of maize cultivation...",
  "time_period": "2500 BCE - 1500 CE",
  "theme": "GEO",
  "node_id": "KC-1.1.I.A"
}
```

## Data Source

**3,347 standards** from [College Board CED](https://apcentral.collegeboard.org/courses/ap-united-states-history):
- APUSH: 1,757 (loaded 2026-02-17)
- APWH: 1,590 (loaded 2026-02-16)

Node ID format: `KC-[Period].[Theme].[Level].[SubLevel]`
