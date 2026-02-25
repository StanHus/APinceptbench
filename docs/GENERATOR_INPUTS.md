# AP Question Generator - Input Reference

Quick reference for all input parameters accepted by the `/generate` endpoint.

---

## Required Parameters

| Field | Type | Values | Description |
|-------|------|--------|-------------|
| `type` | string | `mcq`, `mcq_set`, `saq`, `leq`, `dbq` | Question format to generate |
| `difficulty` | string | `easy`, `medium`, `hard` | Target difficulty level |
| `course` | string | `APUSH`, `APWH` | AP course (US History or World History) |

---

## Curriculum Context

| Field | Type | Example | Description |
|-------|------|---------|-------------|
| `unit` | integer | `1` | Unit number (1-9) |
| `topic` | string | `"Native American Societies Before European Contact"` | Topic/cluster name from curriculum |
| `learning_objective` | string | `"Explain how and why various native populations..."` | Specific learning objective to assess |
| `curriculum_fact` | string | `"The spread of maize cultivation..."` | Core curriculum statement |
| `time_period` | string | `"2500 BCE - 1500 CE"` | Historical time period covered |
| `theme` | string | `"GEO"` | AP theme code (see Theme Codes below) |
| `node_id` | string | `"KC-1.1.I.A"` | Internal curriculum reference ID |

---

## LEQ-Specific

| Field | Type | Values | Description |
|-------|------|--------|-------------|
| `reasoning_type` | string | `causation`, `comparison`, `ccot` | Type of historical reasoning required |

- **causation** - Cause and effect analysis
- **comparison** - Compare/contrast historical developments
- **ccot** - Continuity and Change Over Time

### Historical Thinking Skills (Official AP Framework)

These reasoning types are the **official AP Historical Thinking Skills** defined by College Board:

| Reasoning Type | AP Skill | Description |
|----------------|----------|-------------|
| `causation` | Skill 2: Causation | Describe causes and/or effects of a historical development |
| `comparison` | Skill 3: Comparison | Compare historical developments across time/geography |
| `ccot` | Skill 4: Continuity and Change | Patterns of continuity and/or change over time |

**Source:** [AP History Disciplinary Practices and Reasoning Skills](https://apcentral.collegeboard.org/courses/ap-united-states-history/course)

---

## Example Payloads

### MCQ (Multiple Choice) - APUSH
```json
{
  "type": "mcq",
  "difficulty": "medium",
  "course": "APUSH",
  "unit": 1,
  "topic": "Native American Societies Before European Contact",
  "learning_objective": "Explain how and why various native populations in the period before European contact interacted with the natural environment in North America",
  "curriculum_fact": "The spread of maize cultivation from present day Mexico northward into the present-day American Southwest and beyond supported economic development, settlement, advanced irrigation, and social diversification among societies.",
  "time_period": "2500 BCE - 1500 CE",
  "theme": "GEO",
  "node_id": "KC-1.1.I.A"
}
```

### LEQ (Long Essay Question) - APWH
```json
{
  "type": "leq",
  "difficulty": "hard",
  "course": "APWH",
  "unit": 1,
  "topic": "Developments in East Asia from c. 1200 to c. 1450",
  "learning_objective": "Explain the systems of government employed by Chinese dynasties and how they developed over time.",
  "curriculum_fact": "Explain how empires and states in Afro-Eurasia demonstrated continuity, innovation, and diversity in the 13th century.",
  "time_period": "",
  "theme": "",
  "node_id": "KC-3.2.I.A+1+A",
  "reasoning_type": "comparison"
}
```

### DBQ (Document-Based Question) - APUSH
```json
{
  "type": "dbq",
  "difficulty": "medium",
  "course": "APUSH",
  "unit": 1,
  "topic": "Native American Societies Before European Contact",
  "learning_objective": "Explain how and why various native populations in the period before European contact interacted with the natural environment in North America",
  "curriculum_fact": "The spread of maize cultivation from present day Mexico northward into the present-day American Southwest and beyond supported economic development, settlement, advanced irrigation, and social diversification among societies.",
  "time_period": "2500 BCE - 1500 CE",
  "theme": "GEO",
  "node_id": "KC-1.1.I.A"
}
```

---

## Question Type Details

| Type | Output | Key Requirements |
|------|--------|------------------|
| `mcq` | Single question + 4 choices | One correct answer, 3 plausible distractors |
| `mcq_set` | Stimulus + 2-3 linked questions | Shared stimulus, each question has 4 choices |
| `saq` | 3-part short answer (a, b, c) | Each part answerable in 1-2 sentences |
| `leq` | Essay prompt | Arguable thesis, multiple valid approaches |
| `dbq` | Prompt + 7 documents | Diverse sources, proper attribution required |

### Question Type Sources (Official AP Exam Format)

These question types match the **official AP History exam formats** as defined by College Board:

| Type | Official Name | AP Exam Section | Source |
|------|---------------|-----------------|--------|
| `mcq` | Multiple Choice | Section I, Part A | [AP US History Exam Format](https://apstudents.collegeboard.org/courses/ap-united-states-history/assessment) |
| `mcq_set` | Stimulus-Based Multiple Choice | Section I, Part A | Same as above — MCQs are grouped with primary/secondary source stimuli |
| `saq` | Short Answer Question | Section I, Part B | 3 questions, each with parts (a), (b), (c) |
| `leq` | Long Essay Question | Section II, Part B | Student chooses 1 of 3 prompts |
| `dbq` | Document-Based Question | Section II, Part A | 7 documents, 60 minutes recommended |

**Official Exam Structure (APUSH & APWH):**
- **Section I Part A**: 55 MCQs in 55 minutes (stimulus-based sets)
- **Section I Part B**: 3 SAQs in 40 minutes
- **Section II Part A**: 1 DBQ in 60 minutes (includes 15-min reading)
- **Section II Part B**: 1 LEQ in 40 minutes (choose 1 of 3)

**References:**
- [AP US History: About the Exam](https://apstudents.collegeboard.org/courses/ap-united-states-history/assessment)
- [AP World History: About the Exam](https://apstudents.collegeboard.org/courses/ap-world-history-modern/assessment)
- [AP History Rubrics (DBQ, LEQ, SAQ)](https://apcentral.collegeboard.org/courses/ap-united-states-history/exam)

---

## Difficulty Guidelines

| Level | Description |
|-------|-------------|
| `easy` | Direct recall, single concept, clear correct answer |
| `medium` | Application of concepts, some analysis required |
| `hard` | Complex synthesis, multiple factors, nuanced distinctions |

---

## Theme Codes (Official AP Themes)

These are the **official AP Course Themes** from College Board's Course and Exam Descriptions:

### APUSH Themes
| Code | Theme |
|------|-------|
| `NAT` | American and National Identity |
| `WXT` | Work, Exchange, and Technology |
| `GEO` | Geography and Environment |
| `MIG` | Migration and Settlement |
| `PCE` | Politics and Power |
| `ARC` | America in the World |
| `ARC` | American and Regional Culture |
| `SOC` | Social Structures |

### APWH Themes
| Code | Theme |
|------|-------|
| `GOV` | Governance |
| `ECN` | Economic Systems |
| `SOC` | Social Interactions and Organization |
| `CDI` | Cultural Developments and Interactions |
| `TEC` | Technology and Innovation |
| `ENV` | Humans and the Environment |

**Source:** [AP US History Themes](https://apcentral.collegeboard.org/courses/ap-united-states-history/course) and [AP World History Themes](https://apcentral.collegeboard.org/courses/ap-world-history/course)

---

## Data Source

Values come from the `facts` collection in MongoDB (`ap_social_studies` database):

| Generator Field | DB Field |
|-----------------|----------|
| `topic` | `cluster` |
| `curriculum_fact` | `statement` |
| `time_period` | `date` |
| `learning_objective` | `learning_objective` |
| `theme` | `theme` |
| `unit` | `unit` |
| `node_id` | `node_id` |
| `course` | `course` |

---

## Curriculum Standards Provenance

### Source Documents

All curriculum data is derived from **College Board AP Course and Exam Description (CED)** frameworks:

**AP US History (APUSH)** — 1,757 standards
| Source File | Facts | Notes |
|-------------|-------|-------|
| `AP US History - Knowledge Schema - SME Tracker (1).xlsx` | 1,325 | Primary CED extraction |
| `Knowledge Schema Generator - AP USH Unit 1.xlsx` | 11 | Unit-specific supplements |
| `Knowledge Schema Generator - AP USH Unit 2.xlsx` | 122 | |
| `Knowledge Schema Generator - AP USH Unit 3.xlsx` | 15 | |
| `Knowledge Schema Generator - AP USH Unit 4.xlsx` | 210 | |
| `Knowledge Schema Generator - AP USH Unit 5.xlsx` | 16 | |
| `Knowledge Schema Generator - AP USH Unit 6.xlsx` | 5 | |
| `Knowledge Schema Generator - AP USH Unit 7.xlsx` | 29 | |
| `Knowledge Schema Generator - AP USH Unit 8.xlsx` | 13 | |
| `Knowledge Schema Generator - AP USH Unit 9.xlsx` | 11 | |

**AP World History (APWH)** — 1,590 standards
| Source File | Facts | Notes |
|-------------|-------|-------|
| `Curriculum Data Model Generator - AP World History.xlsx` | 556 | Primary CED extraction |
| `Knowledge Schema Generator - UNIT 2.xlsx` | 126 | Unit-specific supplements |
| `Knowledge Schema Generator - UNIT 3.xlsx` | 82 | |
| `Knowledge Schema Generator - UNIT 4.xlsx` | 152 | |
| `Knowledge Schema Generator - UNIT 5.xlsx` | 182 | |
| `Knowledge Schema Generator - UNIT 6.xlsx` | 164 | |
| `Knowledge Schema Generator - UNIT 7.xlsx` | 158 | |
| `Knowledge Schema Generator - UNIT 8.xlsx` | 1 | |
| `Knowledge Schema Generator - UNIT 9.xlsx` | 169 | |

### Node ID Format

Node IDs follow College Board's **Knowledge Concept (KC)** numbering system:

```
KC-[Period].[Theme].[Level].[SubLevel]
```

Examples:
- `KC-1.1.I.A` → Period 1, Theme 1, Roman numeral I, Letter A
- `KC-3.2.I.A+1+A` → Period 3, Theme 2, with additional substandard notation

### Official References

- **AP US History Course and Exam Description**: [College Board APUSH CED](https://apcentral.collegeboard.org/courses/ap-united-states-history)
- **AP World History Course and Exam Description**: [College Board APWH CED](https://apcentral.collegeboard.org/courses/ap-world-history)

### Data Loaded

| Course | Loaded | Total Facts |
|--------|--------|-------------|
| APWH | 2026-02-16 | 1,590 |
| APUSH | 2026-02-17 | 1,757 |

**Total: 3,347 curriculum standards**

---

*Last updated: 2026-02-25*
