"""
Question Hashing - SHA256 for Reproducibility

Creates deterministic hashes of question content to ensure:
1. Same question always produces same hash
2. Evaluation results can be cached and verified
3. Question identity is tracked across evaluations
"""

import hashlib
import json
from typing import Dict, Any, List, Optional


def normalize_content(content: Any) -> str:
    """
    Normalize content for consistent hashing.

    Handles dictionaries, lists, and strings. Sorts dict keys for determinism.
    """
    if isinstance(content, dict):
        # Sort keys and recursively normalize values
        sorted_items = sorted(
            (k, normalize_content(v)) for k, v in content.items()
        )
        return json.dumps(sorted_items, ensure_ascii=True)
    elif isinstance(content, list):
        return json.dumps([normalize_content(item) for item in content], ensure_ascii=True)
    elif isinstance(content, str):
        # Normalize whitespace
        return " ".join(content.split())
    elif content is None:
        return "null"
    else:
        return str(content)


def hash_question(
    question: str,
    answer: Optional[str] = None,
    answer_options: Optional[List[Dict[str, str]]] = None,
    explanation: Optional[str] = None,
    question_type: Optional[str] = None,
    **kwargs
) -> str:
    """
    Generate SHA256 hash for a question.

    The hash includes the core question content that affects evaluation:
    - Question text
    - Answer
    - Answer options (for MCQ/MSQ)
    - Explanation
    - Question type

    Additional fields in kwargs are ignored (e.g., metadata, timestamps).

    Args:
        question: The question text
        answer: The correct answer
        answer_options: List of answer options (for MCQ/MSQ)
        explanation: The explanation text
        question_type: Type of question (mcq, msq, etc.)
        **kwargs: Additional fields (ignored in hash)

    Returns:
        SHA256 hex digest (64 characters)
    """
    # Build content dictionary with normalized values
    content = {
        "question": normalize_content(question),
        "answer": normalize_content(answer) if answer else "",
        "question_type": normalize_content(question_type) if question_type else "",
    }

    # Add answer options if present
    if answer_options:
        # Sort options by key for determinism
        if isinstance(answer_options, list):
            sorted_options = sorted(
                answer_options,
                key=lambda x: x.get("key", "") if isinstance(x, dict) else str(x)
            )
            content["answer_options"] = normalize_content(sorted_options)

    # Add explanation if present
    if explanation:
        content["explanation"] = normalize_content(explanation)

    # Create deterministic JSON string
    canonical = json.dumps(content, sort_keys=True, ensure_ascii=True)

    # Generate SHA256 hash
    return hashlib.sha256(canonical.encode('utf-8')).hexdigest()


def hash_question_dict(question_dict: Dict[str, Any]) -> str:
    """
    Generate SHA256 hash from a question dictionary.

    Convenience wrapper that extracts standard fields from a dict.

    Args:
        question_dict: Dictionary containing question data

    Returns:
        SHA256 hex digest (64 characters)
    """
    return hash_question(
        question=question_dict.get("question", ""),
        answer=question_dict.get("answer"),
        answer_options=question_dict.get("answer_options"),
        explanation=question_dict.get("explanation"),
        question_type=question_dict.get("type") or question_dict.get("question_type"),
    )


def verify_hash(question_dict: Dict[str, Any], expected_hash: str) -> bool:
    """
    Verify that a question's hash matches expected value.

    Used for detecting if question content has changed since last evaluation.

    Args:
        question_dict: Dictionary containing question data
        expected_hash: Previously computed hash

    Returns:
        True if hashes match, False otherwise
    """
    actual_hash = hash_question_dict(question_dict)
    return actual_hash == expected_hash
