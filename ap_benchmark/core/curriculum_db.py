"""
Curriculum Data Access Layer - MongoDB Integration

Provides functions to fetch curriculum facts from the ap_social_studies.facts
collection. Includes caching with TTL to avoid repeated DB calls during batch
evaluation.

Document Structure (from MongoDB):
{
    "node_id": "KC-1.1.I.A",           # Standard ID (lookup key)
    "course": "APUSH",                  # APUSH or APWH
    "unit": 1,                          # Unit number (1-9)
    "cluster": "Native American...",    # Topic cluster
    "learning_objective": "Explain...", # What students should learn
    "statement": "The spread of...",    # The curriculum fact
    "historical_development": "...",    # Additional context
    "classification": "essential",      # essential or supporting
    "theme": "GEO",                     # Theme code
    "date": "2500 BCE - 1500 CE"        # Time period
}
"""

import logging
import re
import time
from typing import Any, Dict, List, Optional

from .database import get_facts_collection

logger = logging.getLogger(__name__)

# Cache configuration
_cache: Dict[str, tuple] = {}  # key -> (value, timestamp)
CACHE_TTL_SECONDS = 300  # 5 minutes


def _get_cached(key: str) -> Optional[Any]:
    """Get value from cache if not expired."""
    if key in _cache:
        value, timestamp = _cache[key]
        if time.time() - timestamp < CACHE_TTL_SECONDS:
            return value
        del _cache[key]
    return None


def _set_cached(key: str, value: Any) -> None:
    """Set value in cache with current timestamp."""
    _cache[key] = (value, time.time())


def clear_cache() -> None:
    """Clear the entire cache."""
    global _cache
    _cache = {}


def get_fact_by_node_id(node_id: str) -> Optional[Dict[str, Any]]:
    """
    Fetch a single curriculum fact by its node_id.

    Args:
        node_id: The node_id to look up (e.g., "KC-1.1.I.A")

    Returns:
        The fact document or None if not found
    """
    cache_key = f"node:{node_id}"
    cached = _get_cached(cache_key)
    if cached is not None:
        return cached

    collection = get_facts_collection()
    if collection is None:
        return None

    try:
        fact = collection.find_one({"node_id": node_id})
        if fact:
            # Remove MongoDB _id for cleaner output
            fact.pop("_id", None)
            _set_cached(cache_key, fact)
        return fact
    except Exception as e:
        logger.warning(f"Error fetching fact by node_id {node_id}: {e}")
        return None


def get_facts_by_course_unit(course: str, unit: int) -> List[Dict[str, Any]]:
    """
    Fetch all facts for a specific course and unit.

    Args:
        course: Course code (e.g., "APUSH", "APWH")
        unit: Unit number (1-9)

    Returns:
        List of fact documents
    """
    cache_key = f"course_unit:{course}:{unit}"
    cached = _get_cached(cache_key)
    if cached is not None:
        return cached

    collection = get_facts_collection()
    if collection is None:
        return []

    try:
        facts = list(collection.find(
            {"course": course, "unit": unit},
            {"_id": 0}
        ))
        _set_cached(cache_key, facts)
        return facts
    except Exception as e:
        logger.warning(f"Error fetching facts for {course} unit {unit}: {e}")
        return []


def get_facts_by_cluster(course: str, cluster: str) -> List[Dict[str, Any]]:
    """
    Fetch all facts for a specific course and topic cluster.

    Args:
        course: Course code (e.g., "APUSH", "APWH")
        cluster: Topic cluster name

    Returns:
        List of fact documents
    """
    cache_key = f"cluster:{course}:{cluster}"
    cached = _get_cached(cache_key)
    if cached is not None:
        return cached

    collection = get_facts_collection()
    if collection is None:
        return []

    try:
        facts = list(collection.find(
            {"course": course, "cluster": cluster},
            {"_id": 0}
        ))
        _set_cached(cache_key, facts)
        return facts
    except Exception as e:
        logger.warning(f"Error fetching facts for cluster {cluster}: {e}")
        return []


def get_related_facts(node_id: str, limit: int = 5) -> List[Dict[str, Any]]:
    """
    Fetch facts related to a given node_id.

    Finds facts in the same unit and cluster as the target fact.

    Args:
        node_id: The reference node_id
        limit: Maximum number of related facts to return

    Returns:
        List of related fact documents
    """
    cache_key = f"related:{node_id}:{limit}"
    cached = _get_cached(cache_key)
    if cached is not None:
        return cached

    # First get the reference fact
    ref_fact = get_fact_by_node_id(node_id)
    if not ref_fact:
        return []

    collection = get_facts_collection()
    if collection is None:
        return []

    try:
        # Find facts in the same course, unit, and cluster
        facts = list(collection.find(
            {
                "course": ref_fact.get("course"),
                "unit": ref_fact.get("unit"),
                "cluster": ref_fact.get("cluster"),
                "node_id": {"$ne": node_id}  # Exclude the reference fact
            },
            {"_id": 0}
        ).limit(limit))
        _set_cached(cache_key, facts)
        return facts
    except Exception as e:
        logger.warning(f"Error fetching related facts for {node_id}: {e}")
        return []


def search_facts(query: str, course: Optional[str] = None, limit: int = 10) -> List[Dict[str, Any]]:
    """
    Search facts by text query.

    Searches in statement, learning_objective, and cluster fields.

    Args:
        query: Search query string
        course: Optional course filter (e.g., "APUSH")
        limit: Maximum number of results

    Returns:
        List of matching fact documents
    """
    collection = get_facts_collection()
    if collection is None:
        return []

    try:
        # Build the search filter
        search_regex = {"$regex": query, "$options": "i"}
        or_conditions = [
            {"statement": search_regex},
            {"learning_objective": search_regex},
            {"cluster": search_regex},
        ]

        filter_query: Dict[str, Any] = {"$or": or_conditions}
        if course:
            filter_query["course"] = course

        facts = list(collection.find(
            filter_query,
            {"_id": 0}
        ).limit(limit))
        return facts
    except Exception as e:
        logger.warning(f"Error searching facts for '{query}': {e}")
        return []


def parse_node_id(node_id: str) -> Optional[Dict[str, Any]]:
    """
    Parse a MongoDB node_id to extract course and unit info.

    Supports the KC-X.X.X.X format from MongoDB:
    - KC-1.1.I.A -> unit 1
    - KC-3.2.II.B -> unit 3

    Args:
        node_id: The node_id string (e.g., "KC-1.1.I.A")

    Returns:
        Dict with parsed components or None if invalid
    """
    if not node_id:
        return None

    # Match KC-X.Y.Z.W format where X is the unit number
    match = re.match(r"KC-(\d+)\.(\d+)\.([IVX]+)\.([A-Z])", node_id, re.IGNORECASE)
    if match:
        return {
            "node_id": node_id,
            "unit": int(match.group(1)),
            "subunit": int(match.group(2)),
            "section": match.group(3).upper(),
            "subsection": match.group(4).upper(),
            "parsed": True,
        }

    # Try simpler KC-X.Y format
    match = re.match(r"KC-(\d+)\.(\d+)", node_id, re.IGNORECASE)
    if match:
        return {
            "node_id": node_id,
            "unit": int(match.group(1)),
            "subunit": int(match.group(2)),
            "parsed": True,
        }

    return None


def get_fact_context_string(fact: Dict[str, Any]) -> str:
    """
    Convert a fact document to a formatted context string for evaluation.

    Args:
        fact: The fact document from MongoDB

    Returns:
        Formatted string suitable for inclusion in evaluation prompt
    """
    lines = []

    if fact.get("cluster"):
        lines.append(f"**Topic Cluster:** {fact['cluster']}")

    if fact.get("learning_objective"):
        lines.append(f"**Learning Objective:** {fact['learning_objective']}")

    if fact.get("statement"):
        lines.append(f"**Curriculum Statement:** {fact['statement']}")

    if fact.get("historical_development"):
        lines.append(f"**Historical Development:** {fact['historical_development']}")

    if fact.get("date"):
        lines.append(f"**Time Period:** {fact['date']}")

    if fact.get("theme"):
        lines.append(f"**Theme:** {fact['theme']}")

    if fact.get("classification"):
        lines.append(f"**Classification:** {fact['classification']}")

    return "\n".join(lines)
