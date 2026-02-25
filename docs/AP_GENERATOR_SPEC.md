# AP Question Generator Specification

**Version:** 2026.02.24.1
**Source:** College Board AP Central Official Guidelines

This document defines the exact format, structure, and length requirements for generating each official AP question type.

---

## Quick Reference

| Question Type | Course(s) | Output Fields | Complexity |
|---------------|-----------|---------------|------------|
| MCQ | All | stem, options[4], answer, explanation | Low |
| MCQ Set | All | stimulus, questions[3-4] | Medium |
| SAQ | History | prompt, parts[3], scoring_guide | Medium |
| DBQ | History | prompt, documents[7], rubric | High |
| LEQ | History | prompt, reasoning_type, rubric | Medium |
| Concept Application | APGOV | scenario, parts[3-4] | Medium |
| Quantitative | APGOV | data, parts[3-4] | Medium |
| SCOTUS Comparison | APGOV | case, parts[4] | Medium |
| Argument Essay | APGOV | prompt, foundational_docs | Medium |
| APHG FRQ | APHG | stimuli[0-2], parts[7] | Medium |

---

## 1. MCQ - Multiple Choice Question

### Structure

```json
{
  "type": "mcq",
  "stimulus": {                          // Optional - for stimulus-based questions
    "type": "primary_source|secondary_source|image|map|chart|political_cartoon",
    "source": "Author/Publication Name",
    "date": "1850",
    "title": "Title of Document",        // Optional
    "content": "The actual text or description..."
  },
  "question": "Based on the passage, which of the following...",
  "answer_options": [
    {"key": "A", "text": "First option"},
    {"key": "B", "text": "Second option"},
    {"key": "C", "text": "Third option"},
    {"key": "D", "text": "Fourth option"}
  ],
  "answer": "B",
  "explanation": "Option B is correct because...",
  "skill": "causation|comparison|contextualization|sourcing|argumentation",
  "difficulty": "easy|medium|hard"
}
```

### Length Requirements

| Field | Min | Max | Notes |
|-------|-----|-----|-------|
| `stimulus.content` | 50 words | 300 words | Primary sources can be excerpts |
| `question` | 10 words | 50 words | Clear, single question |
| `answer_options[].text` | 5 words | 40 words | Parallel structure required |
| `explanation` | 50 words | 150 words | Explain why correct AND why others wrong |

### Rules

1. **Exactly 4 options** (A, B, C, D)
2. **One unambiguously correct answer**
3. **Distractors must be plausible** - represent real misconceptions
4. **No absolute language** ("always", "never", "all", "none") unless historically accurate
5. **Parallel grammatical structure** across all options
6. **Stimulus-based MCQs** should require analysis, not just reading comprehension

### Example

```json
{
  "type": "mcq",
  "stimulus": {
    "type": "primary_source",
    "source": "Frederick Douglass, Speech at Rochester, New York",
    "date": "July 5, 1852",
    "content": "What, to the American slave, is your 4th of July? I answer: a day that reveals to him, more than all other days in the year, the gross injustice and cruelty to which he is the constant victim."
  },
  "question": "Douglass's speech most directly reflects which of the following perspectives?",
  "answer_options": [
    {"key": "A", "text": "Enslaved people were largely unaware of American ideals of liberty"},
    {"key": "B", "text": "The promise of American freedom was hypocritical given the existence of slavery"},
    {"key": "C", "text": "Independence Day celebrations should be abolished entirely"},
    {"key": "D", "text": "Gradual emancipation was the most practical path to ending slavery"}
  ],
  "answer": "B",
  "explanation": "Option B is correct because Douglass highlights the contradiction between celebrating freedom while millions remained enslaved. He is not arguing that enslaved people were unaware (A), that July 4th should be abolished (C), or advocating for gradual emancipation (D). His speech emphasizes the hypocrisy of the celebration.",
  "skill": "sourcing",
  "difficulty": "medium"
}
```

---

## 2. MCQ Stimulus Set

For efficiency, AP exams often present 3-4 MCQs tied to a single stimulus.

### Structure

```json
{
  "type": "mcq_set",
  "stimulus": {
    "type": "primary_source|secondary_source|image|map|chart|data_table",
    "source": "Full attribution",
    "date": "Date",
    "title": "Title if applicable",
    "content": "The stimulus content..."
  },
  "questions": [
    {
      "question": "Question 1...",
      "answer_options": [...],
      "answer": "A",
      "explanation": "...",
      "skill": "sourcing"
    },
    {
      "question": "Question 2...",
      "answer_options": [...],
      "answer": "C",
      "explanation": "...",
      "skill": "causation"
    },
    {
      "question": "Question 3...",
      "answer_options": [...],
      "answer": "B",
      "explanation": "...",
      "skill": "contextualization"
    }
  ]
}
```

### Rules

1. **3-4 questions per stimulus**
2. **Questions should test different skills** (sourcing, causation, comparison, etc.)
3. **Questions should be independent** - answering one shouldn't reveal another
4. **Stimulus must support all questions**

---

## 3. SAQ - Short Answer Question

### Structure

```json
{
  "type": "saq",
  "stimulus": {                          // Optional - SAQ 1-2 have stimulus, SAQ 3-4 do not
    "type": "primary_source|secondary_source|image|chart|historian_argument",
    "source": "Attribution",
    "date": "Date",
    "content": "Stimulus content..."
  },
  "prompt": "Use the passage above and your knowledge of United States history to answer parts (a), (b), and (c).",
  "parts": [
    {
      "letter": "a",
      "task": "Identify ONE claim made by the author about...",
      "task_verb": "identify",
      "scoring_criteria": "Acceptable responses include...",
      "sample_response": "The author claims that..."
    },
    {
      "letter": "b",
      "task": "Explain ONE piece of historical evidence that supports the author's argument.",
      "task_verb": "explain",
      "scoring_criteria": "Response must provide specific evidence AND explain how it supports...",
      "sample_response": "The passage of the Homestead Act of 1862..."
    },
    {
      "letter": "c",
      "task": "Explain ONE piece of historical evidence that challenges the author's argument.",
      "task_verb": "explain",
      "scoring_criteria": "Response must provide specific evidence AND explain how it challenges...",
      "sample_response": "The continued resistance of Native Americans..."
    }
  ],
  "time_period": "1800-1848",
  "topic": "Westward Expansion",
  "skill": "causation|comparison|contextualization"
}
```

### Length Requirements

| Field | Min | Max | Notes |
|-------|-----|-----|-------|
| `stimulus.content` | 75 words | 250 words | Focused excerpt with clear argument |
| `parts[].task` | 15 words | 40 words | One clear task per part |
| `parts[].sample_response` | 30 words | 75 words | 3-4 sentences expected from student |
| `scoring_criteria` | 20 words | 60 words | Clear what earns the point |

### Task Verbs (Official AP)

| Verb | Definition | Points |
|------|------------|--------|
| **Identify** | Name or point to without explanation | 1 |
| **Describe** | Provide relevant characteristics | 1 |
| **Explain** | Provide how or why with reasoning | 1 |
| **Compare** | Similarities AND differences | 1 |

### Rules

1. **Exactly 3 parts: (a), (b), (c)**
2. **Each part worth exactly 1 point**
3. **Parts must be independently scorable**
4. **Each part requires SPECIFIC historical evidence**
5. **Task verbs must match point value** (identify=1pt, explain=1pt)
6. **No part should be answerable with generalizations**

### Example

```json
{
  "type": "saq",
  "stimulus": {
    "type": "historian_argument",
    "source": "Eric Foner, Reconstruction: America's Unfinished Revolution",
    "date": "1988",
    "content": "Reconstruction was a period of remarkable political innovation, as African Americans voted in large numbers, served in state legislatures and Congress, and helped write new state constitutions. Yet the failure to redistribute land meant that economic power remained concentrated in the hands of former slaveholders."
  },
  "prompt": "Use the passage above and your knowledge of United States history to answer parts (a), (b), and (c).",
  "parts": [
    {
      "letter": "a",
      "task": "Identify ONE political achievement of African Americans during Reconstruction mentioned by Foner.",
      "task_verb": "identify",
      "scoring_criteria": "Acceptable: voting in large numbers, serving in legislatures/Congress, helping write constitutions",
      "sample_response": "African Americans served in state legislatures and in Congress during Reconstruction."
    },
    {
      "letter": "b",
      "task": "Explain ONE reason why the failure to redistribute land limited African American freedom after the Civil War.",
      "task_verb": "explain",
      "scoring_criteria": "Must explain causal relationship between land ownership and freedom/economic independence",
      "sample_response": "Without land ownership, formerly enslaved people had to work as sharecroppers on land owned by former slaveholders. This created a system of debt peonage that kept African Americans economically dependent and limited their ability to achieve true independence."
    },
    {
      "letter": "c",
      "task": "Explain ONE way that Reconstruction's political achievements were reversed after 1877.",
      "task_verb": "explain",
      "scoring_criteria": "Must provide specific example of reversal AND explain how it undid political gains",
      "sample_response": "After the Compromise of 1877, Southern states implemented Jim Crow laws and literacy tests that effectively disenfranchised African American voters. This reversed the political participation Foner describes, as Black voter registration dropped dramatically by the 1890s."
    }
  ],
  "time_period": "1865-1898",
  "topic": "Reconstruction",
  "skill": "causation"
}
```

---

## 4. DBQ - Document-Based Question

### Structure

```json
{
  "type": "dbq",
  "prompt": "Evaluate the extent to which [historical development] changed [aspect] during [time period].",
  "time_period": "1800-1848",
  "topic": "Topic Name",
  "task_verb": "evaluate|analyze|explain|compare",
  "documents": [
    {
      "number": 1,
      "type": "primary_source|government_document|letter|speech|newspaper|image|map|chart",
      "source": "Full attribution with author if known",
      "author": "Author Name",
      "date": "Specific date or year",
      "title": "Document title",
      "context": "Brief historical context for sourcing",
      "content": "The actual document text or image description...",
      "perspective": "Supports thesis A|Supports thesis B|Complicates argument"
    }
    // ... 7 documents total
  ],
  "suggested_thesis_positions": [
    "Position A: [historical change was significant because...]",
    "Position B: [historical change was limited because...]",
    "Position C: [nuanced - change was significant in X but limited in Y]"
  ],
  "suggested_outside_evidence": [
    "Evidence 1 not in documents",
    "Evidence 2 not in documents",
    "Evidence 3 not in documents"
  ],
  "contextualization_suggestions": [
    "Broader development 1",
    "Broader development 2"
  ],
  "scoring_notes": {
    "thesis": "Must take a position on extent of change",
    "context": "Should reference developments before or during period",
    "evidence": "4+ documents for full credit",
    "sourcing": "HIPP analysis for 2+ documents",
    "complexity": "Nuanced argument OR all 7 docs + HIPP on 4"
  }
}
```

### Document Requirements

| Requirement | Specification |
|-------------|---------------|
| **Total documents** | Exactly 7 |
| **Document types** | Mix of: primary, secondary, visual, quantitative |
| **Perspectives** | At least 2-3 different viewpoints |
| **Usability** | Each document must be usable for argument |
| **Attribution** | Author, date, source for each |
| **Length per doc** | 50-200 words (can excerpt longer documents) |

### Document Type Distribution (Recommended)

```
Primary text sources:     3-4 documents
Secondary sources:        0-1 documents
Visual sources:           1-2 documents (maps, images, cartoons)
Quantitative sources:     0-1 documents (charts, tables, data)
```

### Length Requirements

| Field | Min | Max | Notes |
|-------|-----|-----|-------|
| `prompt` | 20 words | 50 words | Clear argumentative task |
| `documents[].content` | 50 words | 200 words | Focused excerpt |
| `documents[].context` | 15 words | 40 words | For HIPP analysis |
| Total document text | 500 words | 1200 words | All 7 documents combined |

### Prompt Formulas (Official AP Style)

```
"Evaluate the extent to which [development] [changed/affected] [aspect] during [period]."

"Analyze the [causes/effects] of [development] during [period]."

"Compare and contrast [X] and [Y] during [period]."

"Analyze the [reasons/ways] that [development] [affected/shaped] [aspect] during [period]."
```

### Rules

1. **Exactly 7 documents** - no more, no less
2. **Multiple perspectives required** - documents must allow different arguments
3. **Arguable prompt** - multiple defensible thesis positions must exist
4. **HIPP-able documents** - each document must have identifiable POV, purpose, audience, or situation
5. **Specific time period** - prompt must specify date range
6. **Usable documents** - every document must be relevant and usable

### Example Document

```json
{
  "number": 3,
  "type": "government_document",
  "source": "Indian Removal Act",
  "author": "United States Congress",
  "date": "May 28, 1830",
  "title": "An Act to provide for an exchange of lands with the Indians",
  "context": "Passed during Andrew Jackson's presidency with strong Southern support",
  "content": "Be it enacted... That it shall and may be lawful for the President of the United States to cause so much of any territory belonging to the United States, west of the river Mississippi... to be divided into a suitable number of districts, for the reception of such tribes or nations of Indians as may choose to exchange the lands where they now reside, and remove there.",
  "perspective": "Government justification for removal policy"
}
```

---

## 5. LEQ - Long Essay Question

### Structure

```json
{
  "type": "leq",
  "prompt": "Evaluate the extent to which [development] represented a [continuity/change] in [aspect] during [period].",
  "time_period": "1800-1848",
  "reasoning_type": "causation|comparison|continuity_and_change",
  "topic": "Topic Name",
  "thesis_positions": [
    "Position 1: Strong continuity because...",
    "Position 2: Significant change because...",
    "Position 3: Nuanced - continuity in X, change in Y"
  ],
  "suggested_evidence": [
    "Specific historical example 1",
    "Specific historical example 2",
    "Specific historical example 3",
    "Specific historical example 4"
  ],
  "contextualization_suggestions": [
    "Broader development for context"
  ],
  "complexity_opportunities": [
    "Could compare across regions",
    "Could analyze multiple causes",
    "Could address counterargument"
  ],
  "scoring_notes": {
    "thesis": "Must establish clear line of reasoning",
    "context": "Situate in broader developments",
    "evidence": "3-4 specific examples needed",
    "reasoning": "Must use specified reasoning type",
    "complexity": "Nuance through contradiction, comparison, or synthesis"
  }
}
```

### Reasoning Type Requirements

| Type | Prompt Keywords | Student Must Do |
|------|-----------------|-----------------|
| **Causation** | "causes", "effects", "led to", "resulted in" | Explain cause-effect relationships |
| **Comparison** | "compare", "contrast", "similarities", "differences" | Identify AND explain similarities/differences |
| **CCOT** | "continuity", "change", "over time", "extent" | Analyze what stayed same AND what changed |

### Length Requirements

| Field | Min | Max | Notes |
|-------|-----|-----|-------|
| `prompt` | 20 words | 50 words | Clear argumentative task |
| `thesis_positions[]` | 15 words | 40 words | Each position |
| `suggested_evidence[]` | 5 words | 20 words | Specific examples |

### Prompt Formulas by Reasoning Type

**Causation:**
```
"Evaluate the extent to which [factor] caused [development] during [period]."
"Analyze the [causes/effects] of [development] during [period]."
```

**Comparison:**
```
"Compare and contrast [X] and [Y] during [period]."
"Analyze similarities and differences between [X] and [Y]."
```

**Continuity and Change:**
```
"Evaluate the extent to which [aspect] changed during [period]."
"Analyze continuities and changes in [aspect] from [period] to [period]."
```

### Rules

1. **No documents provided** - relies on student knowledge
2. **Clear reasoning type** - must be obviously causation, comparison, or CCOT
3. **Specific time period** - must specify date range
4. **Arguable** - multiple valid thesis positions
5. **Evidence accessible** - students can cite specific examples from curriculum

---

## 6. AP Government FRQs

### 6a. Concept Application

```json
{
  "type": "apgov_concept_application",
  "scenario": "A state legislature passes a law requiring all social media companies to verify the age of users and restrict access for those under 16. Several technology companies file a lawsuit claiming the law violates their First Amendment rights.",
  "parts": [
    {
      "letter": "a",
      "task": "Describe the constitutional principle that the technology companies would most likely invoke in their lawsuit.",
      "task_verb": "describe",
      "points": 1
    },
    {
      "letter": "b",
      "task": "Explain how the precedent set in Tinker v. Des Moines could be used by either side in this case.",
      "task_verb": "explain",
      "points": 2
    },
    {
      "letter": "c",
      "task": "Explain one way the outcome of this case could affect the relationship between state governments and the federal government.",
      "task_verb": "explain",
      "points": 1
    }
  ],
  "concepts_tested": ["First Amendment", "federalism", "judicial review"],
  "total_points": 4
}
```

### 6b. Quantitative Analysis

```json
{
  "type": "apgov_quantitative",
  "data": {
    "type": "bar_chart|line_graph|table|pie_chart",
    "title": "Voter Turnout by Age Group, 2008-2024",
    "source": "U.S. Census Bureau",
    "description": "Bar chart showing voter turnout percentages for ages 18-29, 30-44, 45-64, and 65+ across presidential elections from 2008 to 2024.",
    "values": {
      "2008": {"18-29": 51, "30-44": 62, "45-64": 69, "65+": 72},
      "2012": {"18-29": 45, "30-44": 60, "45-64": 68, "65+": 72},
      "2016": {"18-29": 46, "30-44": 59, "45-64": 66, "65+": 71},
      "2020": {"18-29": 52, "30-44": 63, "45-64": 69, "65+": 74},
      "2024": {"18-29": 48, "30-44": 61, "45-64": 68, "65+": 73}
    }
  },
  "parts": [
    {
      "letter": "a",
      "task": "Identify the age group with the highest voter turnout across all elections shown.",
      "task_verb": "identify",
      "points": 1
    },
    {
      "letter": "b",
      "task": "Describe a trend in voter turnout among 18-29 year olds shown in the data.",
      "task_verb": "describe",
      "points": 1
    },
    {
      "letter": "c",
      "task": "Explain one reason for the pattern in youth voter turnout identified in part (b).",
      "task_verb": "explain",
      "points": 1
    },
    {
      "letter": "d",
      "task": "Explain one way a political party might use this data to develop a campaign strategy.",
      "task_verb": "explain",
      "points": 1
    }
  ],
  "total_points": 4
}
```

### 6c. SCOTUS Comparison

```json
{
  "type": "apgov_scotus",
  "non_required_case": {
    "name": "Carpenter v. United States",
    "year": 2018,
    "facts": "Timothy Carpenter was convicted of robbery based partly on cell phone location data obtained by the FBI without a warrant. The government argued that the third-party doctrine applied because Carpenter had voluntarily shared his location with his cell phone provider.",
    "ruling": "The Supreme Court ruled 5-4 that obtaining cell-site location information constitutes a search under the Fourth Amendment and generally requires a warrant.",
    "constitutional_issue": "Fourth Amendment protection against unreasonable searches"
  },
  "parts": [
    {
      "letter": "a",
      "task": "Identify the constitutional provision that is common to both Carpenter v. United States and United States v. Lopez.",
      "task_verb": "identify",
      "points": 1
    },
    {
      "letter": "b",
      "task": "Describe the ruling in United States v. Lopez.",
      "task_verb": "describe",
      "points": 1
    },
    {
      "letter": "c",
      "task": "Explain one way in which the holding in Carpenter v. United States is similar to or different from the holding in a required Supreme Court case other than United States v. Lopez.",
      "task_verb": "explain",
      "points": 1
    },
    {
      "letter": "d",
      "task": "Explain how Carpenter v. United States relates to the ongoing debate about the balance between national security and civil liberties.",
      "task_verb": "explain",
      "points": 1
    }
  ],
  "relevant_required_cases": ["United States v. Lopez", "Schenck v. United States"],
  "total_points": 4
}
```

### 6d. Argument Essay

```json
{
  "type": "apgov_argument",
  "prompt": "Develop an argument that explains whether the Electoral College should be maintained or replaced with a national popular vote for presidential elections.",
  "foundational_documents": [
    "Federalist No. 68",
    "Constitution, Article II",
    "Federalist No. 10"
  ],
  "thesis_positions": [
    "Electoral College should be maintained because it protects federalism and small states",
    "Electoral College should be replaced because it undermines democratic principles",
    "Electoral College should be reformed but not eliminated"
  ],
  "suggested_evidence": [
    "2000 and 2016 elections where popular vote winner lost",
    "Federalist No. 68 arguments about deliberation",
    "Winner-take-all system effects",
    "National Popular Vote Interstate Compact"
  ],
  "rebuttal_opportunities": [
    "If arguing for EC: address concerns about democratic legitimacy",
    "If arguing against EC: address concerns about small state representation"
  ],
  "total_points": 6
}
```

---

## 7. AP Human Geography FRQs

### Structure by Type

**Type 1 (No Stimulus):**
```json
{
  "type": "aphg_frq",
  "frq_subtype": "type1",
  "stimuli": [],
  "question": "Agricultural practices vary significantly across different regions of the world.",
  "parts": [
    {"letter": "A", "task": "Define intensive subsistence agriculture.", "points": 1},
    {"letter": "B", "task": "Explain ONE reason why intensive subsistence agriculture developed in South and East Asia.", "points": 1},
    {"letter": "C", "task": "Describe ONE characteristic of plantation agriculture.", "points": 1},
    {"letter": "D", "task": "Explain ONE economic factor that influences the location of plantation agriculture.", "points": 1},
    {"letter": "E", "task": "Explain ONE way the Green Revolution changed agricultural practices in developing countries.", "points": 1},
    {"letter": "F", "task": "Describe ONE environmental consequence of the Green Revolution.", "points": 1},
    {"letter": "G", "task": "Explain ONE reason why organic farming has increased in developed countries.", "points": 1}
  ],
  "concepts": ["intensive agriculture", "plantation agriculture", "Green Revolution", "organic farming"],
  "total_points": 7
}
```

**Type 2 (One Stimulus):**
```json
{
  "type": "aphg_frq",
  "frq_subtype": "type2",
  "stimuli": [
    {
      "type": "map|image|chart|data_table",
      "title": "Population Pyramid of Country X, 2020",
      "description": "A population pyramid showing age-sex distribution with a wide base narrowing toward the top, indicating high birth rates and lower life expectancy."
    }
  ],
  "question": "Use the population pyramid and your knowledge of population geography to answer the following.",
  "parts": [
    {"letter": "A", "task": "Identify the stage of the demographic transition model that Country X is most likely in.", "points": 1},
    {"letter": "B", "task": "Describe ONE characteristic of the population pyramid that supports your answer to part A.", "points": 1},
    // ... 7 parts total
  ],
  "concepts": ["demographic transition model", "population pyramids", "dependency ratio"],
  "total_points": 7
}
```

**Type 3 (Two Stimuli):**
```json
{
  "type": "aphg_frq",
  "frq_subtype": "type3",
  "stimuli": [
    {
      "type": "map",
      "title": "Urban Land Use Model A",
      "description": "Concentric zone model showing CBD in center with zones radiating outward"
    },
    {
      "type": "map",
      "title": "Urban Land Use Model B",
      "description": "Sector model showing CBD with wedge-shaped zones extending from center"
    }
  ],
  "question": "The two images above show different models of urban structure.",
  "parts": [
    {"letter": "A", "task": "Identify the urban model shown in Image A.", "points": 1},
    {"letter": "B", "task": "Identify the urban model shown in Image B.", "points": 1},
    {"letter": "C", "task": "Explain ONE similarity between the two models.", "points": 1},
    {"letter": "D", "task": "Explain ONE difference between the two models.", "points": 1},
    // ... 7 parts total
  ],
  "concepts": ["concentric zone model", "sector model", "urban structure"],
  "total_points": 7
}
```

### APHG Task Verb Requirements

| Verb | Points | Student Must Do |
|------|--------|-----------------|
| **Identify** | 1 | Name the concept/feature |
| **Define** | 1 | Provide meaning |
| **Describe** | 1 | Provide characteristics |
| **Explain** | 1 | Provide how or why |
| **Compare** | 2 | Similarities AND differences |

---

## Validation Checklist

Before submitting any generated question, verify:

### All Types
- [ ] Correct JSON structure
- [ ] All required fields present
- [ ] Appropriate length for each field
- [ ] Factual accuracy verified
- [ ] Aligned with curriculum standards

### MCQ
- [ ] Exactly 4 options
- [ ] One correct answer
- [ ] Plausible distractors
- [ ] No absolute language
- [ ] Explanation covers all options

### SAQ
- [ ] Exactly 3 parts (a, b, c)
- [ ] Clear task verb per part
- [ ] Each part independently scorable
- [ ] Requires specific evidence

### DBQ
- [ ] Exactly 7 documents
- [ ] Multiple perspectives represented
- [ ] Full attribution on each document
- [ ] Arguable prompt (multiple valid theses)
- [ ] Documents allow HIPP analysis

### LEQ
- [ ] Clear reasoning type (causation/comparison/CCOT)
- [ ] Specific time period
- [ ] Multiple valid thesis positions
- [ ] Evidence accessible from curriculum

### FRQ (Gov/HumanGeo)
- [ ] Correct number of parts
- [ ] Task verbs match point values
- [ ] Stimulus accurate (if applicable)
- [ ] Concepts clearly testable
