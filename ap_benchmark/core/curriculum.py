"""
Curriculum Context - Dynamic Curriculum-Aware Evaluation

Provides curriculum context for evaluation based on the original request.
Follows InceptBench's confidence level approach:

- GUARANTEED: Explicit skills/substandard metadata provided
- HARD: Generation instructions provided
- SOFT: Content inference only

The curriculum context tells the evaluator what the content SHOULD test,
making evaluation precise and curriculum-aligned.

MongoDB Integration:
When a node_id is provided (e.g., "KC-1.1.I.A"), fetches curriculum facts
from the ap_social_studies.facts collection to enrich evaluation context.
"""

import json
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass

logger = logging.getLogger(__name__)

# AP Course unit topics for context
AP_COURSE_UNITS = {
    "APUSH": {
        1: "Period 1: 1491-1607 (Native Americans & European Contact)",
        2: "Period 2: 1607-1754 (Colonial America)",
        3: "Period 3: 1754-1800 (Revolution & Early Republic)",
        4: "Period 4: 1800-1848 (Democracy & Expansion)",
        5: "Period 5: 1844-1877 (Civil War & Reconstruction)",
        6: "Period 6: 1865-1898 (Gilded Age)",
        7: "Period 7: 1890-1945 (Imperialism to WWII)",
        8: "Period 8: 1945-1980 (Cold War Era)",
        9: "Period 9: 1980-Present (Modern America)",
    },
    "APWH": {
        1: "Unit 1: c. 1200-1450 (Global Tapestry)",
        2: "Unit 2: c. 1450-1750 (Networks of Exchange)",
        3: "Unit 3: c. 1450-1750 (Land-Based Empires)",
        4: "Unit 4: c. 1450-1750 (Maritime Empires)",
        5: "Unit 5: c. 1750-1900 (Revolutions)",
        6: "Unit 6: c. 1750-1900 (Consequences of Industrialization)",
        7: "Unit 7: c. 1900-Present (Global Conflict)",
        8: "Unit 8: c. 1900-Present (Cold War & Decolonization)",
        9: "Unit 9: c. 1900-Present (Globalization)",
    },
    "APGOV": {
        1: "Unit 1: Foundations of American Democracy",
        2: "Unit 2: Interactions Among Branches of Government",
        3: "Unit 3: Civil Liberties and Civil Rights",
        4: "Unit 4: American Political Ideologies and Beliefs",
        5: "Unit 5: Political Participation",
    },
    "APHG": {
        1: "Unit 1: Thinking Geographically",
        2: "Unit 2: Population and Migration",
        3: "Unit 3: Cultural Patterns and Processes",
        4: "Unit 4: Political Patterns and Processes",
        5: "Unit 5: Agriculture and Rural Land-Use",
        6: "Unit 6: Cities and Urban Land-Use",
        7: "Unit 7: Industrial and Economic Development",
    },
    "APEH": {
        1: "Unit 1: c. 1450-1648 (Renaissance & Exploration)",
        2: "Unit 2: c. 1648-1815 (Age of Absolutism)",
        3: "Unit 3: c. 1815-1914 (Industrialization & Society)",
        4: "Unit 4: c. 1914-Present (Global Wars to Present)",
    },
}

# AP History Thinking Skills
AP_THINKING_SKILLS = {
    "causation": "Identify causes and effects of historical developments",
    "comparison": "Compare historical developments across time/place",
    "continuity_change": "Analyze patterns of continuity and change over time",
    "contextualization": "Connect historical developments to broader context",
    "argumentation": "Make and support historical claims with evidence",
    "periodization": "Explain how historical periods are defined and characterized",
    "synthesis": "Combine diverse evidence to make historical arguments",
}


@dataclass
class ConfidenceLevel:
    """Confidence level for curriculum targeting."""
    level: str  # "GUARANTEED", "HARD", or "SOFT"
    source: str  # Description of what determined this level

    def to_prompt_section(self) -> str:
        """Generate prompt section explaining confidence level."""
        if self.level == "GUARANTEED":
            return (
                f"**Confidence: GUARANTEED** (Source: {self.source})\n"
                "The content MUST align with the specified curriculum standard. "
                "Any deviation from the target standard is a curriculum_alignment FAILURE."
            )
        elif self.level == "HARD":
            return (
                f"**Confidence: HARD** (Source: {self.source})\n"
                "The content should align with curriculum standards inferred from the generation request. "
                "Evaluate curriculum alignment strictly based on the provided context."
            )
        else:
            return (
                f"**Confidence: SOFT** (Source: {self.source})\n"
                "Curriculum standards are inferred from content. Be conservative in evaluation - "
                "only fail curriculum_alignment for clear mismatches with AP curriculum."
            )


def parse_substandard_id(substandard_id: str) -> Dict[str, Any]:
    """
    Parse a substandard ID to extract course, unit, and topic info.

    Supports formats:
    - AP.USH.3.1, AP.WH.2.1, AP.GOV.1.1
    - USH.3.1.1, WH.2.1.1

    Returns dict with course, unit, and any extracted metadata.
    """
    import re

    if not substandard_id:
        return {"course": "APUSH", "unit": 1, "parsed": False}

    # Course code mapping
    course_map = {
        'USH': 'APUSH', 'WH': 'APWH', 'GOV': 'APGOV',
        'HG': 'APHG', 'EH': 'APEH', 'EURO': 'APEH',
    }

    # Try AP.XXX.N.N format
    match = re.match(r'AP\.?(USH|WH|GOV|HG|EH|EURO)\.?(\d+)\.?(\d+)?', substandard_id, re.IGNORECASE)
    if match:
        course_code = match.group(1).upper()
        return {
            "course": course_map.get(course_code, "APUSH"),
            "unit": int(match.group(2)),
            "subunit": int(match.group(3)) if match.group(3) else None,
            "parsed": True,
            "raw": substandard_id,
        }

    # Try XXX.N.N.N format (without AP prefix)
    match = re.match(r'(USH|WH|GOV|HG|EH|EURO)\.(\d+)\.?(\d+)?\.?(\d+)?', substandard_id, re.IGNORECASE)
    if match:
        course_code = match.group(1).upper()
        return {
            "course": course_map.get(course_code, "APUSH"),
            "unit": int(match.group(2)),
            "subunit": int(match.group(3)) if match.group(3) else None,
            "parsed": True,
            "raw": substandard_id,
        }

    return {"course": "APUSH", "unit": 1, "parsed": False, "raw": substandard_id}


def get_unit_context(course: str, unit: int) -> str:
    """Get the unit topic description for a course/unit."""
    course_units = AP_COURSE_UNITS.get(course, {})
    return course_units.get(unit, f"Unit {unit}")


def determine_confidence_level(
    substandard_id: Optional[str] = None,
    substandard_description: Optional[str] = None,
    instructions: Optional[str] = None,
    node_id: Optional[str] = None,
) -> ConfidenceLevel:
    """
    Determine confidence level for curriculum targeting.

    Following InceptBench methodology:
    - GUARANTEED: Explicit substandard_id or node_id provided
    - HARD: Generation instructions provided
    - SOFT: Content inference only
    """
    if node_id and node_id.strip():
        return ConfidenceLevel("GUARANTEED", "explicit MongoDB node_id")

    if substandard_id and substandard_id.strip() and substandard_id.upper() != "UNKNOWN":
        return ConfidenceLevel("GUARANTEED", "explicit substandard_id")

    if substandard_description and substandard_description.strip():
        return ConfidenceLevel("HARD", "substandard_description")

    if instructions and instructions.strip():
        return ConfidenceLevel("HARD", "generation instructions")

    return ConfidenceLevel("SOFT", "content inference")


def _fetch_mongodb_context(node_id: str) -> Optional[Dict[str, Any]]:
    """
    Fetch curriculum fact from MongoDB by node_id.

    Returns fact document or None if unavailable.
    """
    try:
        from .curriculum_db import get_fact_by_node_id
        return get_fact_by_node_id(node_id)
    except ImportError:
        logger.warning("curriculum_db module not available")
        return None
    except Exception as e:
        logger.warning(f"Error fetching MongoDB fact for {node_id}: {e}")
        return None


def build_curriculum_context(
    substandard_id: Optional[str] = None,
    node_id: Optional[str] = None,
    substandard_description: Optional[str] = None,
    lesson_title: Optional[str] = None,
    difficulty: str = "medium",
    question_type: str = "mcq",
    instructions: Optional[str] = None,
    fetch_from_db: bool = True,
) -> Tuple[str, ConfidenceLevel]:
    """
    Build comprehensive curriculum context for evaluation.

    Args:
        substandard_id: Standard ID in AP.USH.X.X format
        node_id: MongoDB node_id in KC-X.X.X.X format (takes precedence)
        substandard_description: What skill/concept to test
        lesson_title: Lesson context
        difficulty: Expected difficulty level
        question_type: Expected question format
        instructions: Additional generation instructions
        fetch_from_db: Whether to fetch from MongoDB when node_id provided

    Returns:
        Tuple of (curriculum_context_string, confidence_level)
    """
    # Determine confidence level
    confidence = determine_confidence_level(
        substandard_id, substandard_description, instructions, node_id
    )

    lines = ["## CURRICULUM CONTEXT", ""]
    lines.append(confidence.to_prompt_section())
    lines.append("")

    # Fetch MongoDB fact if node_id provided
    mongodb_fact = None
    if node_id and fetch_from_db:
        mongodb_fact = _fetch_mongodb_context(node_id)
        if mongodb_fact:
            logger.info(f"Fetched MongoDB fact for node_id: {node_id}")

    # Add MongoDB-sourced context if available
    if mongodb_fact:
        lines.append(f"**Node ID:** {node_id}")
        lines.append(f"**Course:** {mongodb_fact.get('course', 'Unknown')}")

        unit = mongodb_fact.get('unit')
        course = mongodb_fact.get('course', '')
        if unit and course:
            unit_topic = get_unit_context(course, unit)
            lines.append(f"**Unit:** {unit_topic}")

        if mongodb_fact.get('cluster'):
            lines.append(f"**Topic Cluster:** {mongodb_fact['cluster']}")

        if mongodb_fact.get('learning_objective'):
            lines.append(f"**Learning Objective:** {mongodb_fact['learning_objective']}")

        if mongodb_fact.get('statement'):
            lines.append(f"**Curriculum Statement:** {mongodb_fact['statement']}")

        if mongodb_fact.get('historical_development'):
            lines.append(f"**Historical Development:** {mongodb_fact['historical_development']}")

        if mongodb_fact.get('date'):
            lines.append(f"**Time Period:** {mongodb_fact['date']}")

        if mongodb_fact.get('theme'):
            lines.append(f"**Theme:** {mongodb_fact['theme']}")

        if mongodb_fact.get('classification'):
            classification = mongodb_fact['classification']
            lines.append(f"**Classification:** {classification}")
            if classification == "essential":
                lines.append("  - This is an ESSENTIAL curriculum fact that students must know")

        lines.append("")

    # Fall back to substandard_id parsing if no MongoDB data
    elif substandard_id and substandard_id.upper() != "UNKNOWN":
        parsed = parse_substandard_id(substandard_id)

        if parsed.get("parsed"):
            course = parsed["course"]
            unit = parsed["unit"]
            unit_topic = get_unit_context(course, unit)

            lines.append(f"**Target Standard:** {substandard_id}")
            lines.append(f"**Course:** {course}")
            lines.append(f"**Unit:** {unit_topic}")
            lines.append("")
        else:
            lines.append(f"**Target Standard:** {substandard_id}")
            lines.append("")

    # Add skill description (can supplement MongoDB data)
    if substandard_description:
        lines.append(f"**Skill/Concept to Test:** {substandard_description}")
        lines.append("")

    # Add lesson context
    if lesson_title:
        lines.append(f"**Lesson Context:** {lesson_title}")
        lines.append("")

    # Add difficulty expectation
    difficulty_expectations = {
        "easy": "Should test basic recall and comprehension of key concepts",
        "medium": "Should require analysis, application, or synthesis of concepts",
        "hard": "Should require evaluation, complex analysis, or multiple concepts",
    }
    lines.append(f"**Expected Difficulty:** {difficulty}")
    lines.append(f"  - {difficulty_expectations.get(difficulty, difficulty_expectations['medium'])}")
    lines.append("")

    # Add question type expectations
    type_expectations = {
        "mcq": "Multiple choice with 4 options, 1 correct answer",
        "msq": "Multiple select with 5 options, 2-3 correct answers",
        "fill-in": "Fill-in-the-blank testing key vocabulary/concepts",
        "match": "Matching exercise connecting related concepts",
        "article": "Educational article covering the topic in depth",
    }
    lines.append(f"**Expected Format:** {question_type}")
    lines.append(f"  - {type_expectations.get(question_type, question_type)}")
    lines.append("")

    # Add special instructions if provided
    if instructions:
        lines.append("**Special Instructions:**")
        lines.append(instructions)
        lines.append("")

    # Add AP-specific thinking skills reminder
    lines.append("**AP Thinking Skills Expected:**")
    lines.append("  - Questions should test historical thinking, not just factual recall")
    lines.append("  - Look for causation, comparison, contextualization, or argumentation")
    lines.append("")

    return "\n".join(lines), confidence


def get_curriculum_facts_for_standard(
    substandard_id: str,
    curriculum_data_path: Optional[Path] = None,
) -> List[Dict[str, Any]]:
    """
    Load curriculum facts relevant to a standard from local JSON.

    This provides authoritative curriculum content for evaluation.
    """
    if not curriculum_data_path:
        # Default path
        base = Path(__file__).parent.parent.parent.parent
        curriculum_data_path = base / "docs" / "curriculum-facts-export.json"

    if not curriculum_data_path.exists():
        logger.warning(f"Curriculum data not found at {curriculum_data_path}")
        return []

    try:
        with open(curriculum_data_path, 'r') as f:
            all_facts = json.load(f)

        # Parse the target standard
        parsed = parse_substandard_id(substandard_id)
        if not parsed.get("parsed"):
            return []

        # Filter facts by course and unit
        relevant = []
        for fact in all_facts:
            if (fact.get("course") == parsed["course"] and
                fact.get("unit") == parsed["unit"]):
                relevant.append(fact)

        return relevant[:10]  # Limit to 10 most relevant

    except Exception as e:
        logger.warning(f"Error loading curriculum facts: {e}")
        return []
