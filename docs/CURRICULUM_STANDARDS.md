# Curriculum Standards

**3,347 standards** in MongoDB `ap_social_studies.facts`

| Course | Units | Facts |
|--------|-------|-------|
| APUSH | 9 | 1,757 |
| APWH | 10 | 1,590 |

## Schema

```javascript
{
  course: "APUSH" | "APWH",
  unit: 1-9,
  cluster: "Topic Name",
  statement: "Curriculum fact text",
  learning_objective: "LO text",
  theme: "GEO" | "MIG" | "SOC" | ...,
  node_id: "KC-1.1.I.A",
  date: "Time period"
}
```

## Sources

Data extracted from College Board Course and Exam Descriptions:
- [APUSH CED](https://apcentral.collegeboard.org/courses/ap-united-states-history)
- [APWH CED](https://apcentral.collegeboard.org/courses/ap-world-history)

## Query Examples

```javascript
// Get all APUSH Unit 3 facts
db.facts.find({ course: "APUSH", unit: 3 })

// Get facts by theme
db.facts.find({ theme: "GEO" })

// Random sample for benchmark
db.facts.aggregate([{ $sample: { size: 200 } }])
```
