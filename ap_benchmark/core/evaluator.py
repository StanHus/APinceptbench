"""
Claude-Based Evaluator - Dynamic, Curriculum-Aware

Uses Claude API with temperature=0.0 for deterministic, reproducible evaluation.
Following InceptBench methodology:

1. Dynamic curriculum context built from request metadata
2. Confidence levels (GUARANTEED/HARD/SOFT) determine strictness
3. Image evaluation support via Claude vision
4. Issue-first methodology with binary scoring

Key principle: The ORIGINAL REQUEST is the ground truth.
"""

import base64
import json
import os
import httpx
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional, Union
import anthropic

from .models import (
    BenchmarkResult,
    DimensionScore,
    HardFailResult,
    QuestionType,
    Issue,
    EvaluationRequest,
)
from .hash import hash_question_dict
from .scorer import calculate_overall_score
from .curriculum import build_curriculum_context, ConfidenceLevel

from ..prompts.base import (
    get_evaluation_prompt,
    format_question_content,
    PROMPT_VERSION,
)
from ..prompts.mcq import MCQ_ADDITIONS
from ..prompts.msq import MSQ_ADDITIONS
from ..prompts.fill_in import FILL_IN_ADDITIONS
from ..prompts.match import MATCH_ADDITIONS
from ..prompts.article import ARTICLE_ADDITIONS
from ..hard_fail.checker import check_hard_fails

logger = logging.getLogger(__name__)

# Singleton client
_client: Optional[anthropic.Anthropic] = None


def get_client() -> anthropic.Anthropic:
    """Get or create singleton Anthropic client."""
    global _client
    if _client is None:
        api_key = os.environ.get("ANTHROPIC_API_KEY")
        if not api_key:
            raise ValueError("ANTHROPIC_API_KEY environment variable not set")
        _client = anthropic.Anthropic(api_key=api_key)
    return _client


# Model for evaluation - Claude Sonnet with vision
EVAL_MODEL = "claude-sonnet-4-6"


TYPE_ADDITIONS = {
    "mcq": MCQ_ADDITIONS,
    "msq": MSQ_ADDITIONS,
    "fill-in": FILL_IN_ADDITIONS,
    "fill_in": FILL_IN_ADDITIONS,
    "match": MATCH_ADDITIONS,
    "article": ARTICLE_ADDITIONS,
}


def _load_image_as_base64(image_path_or_url: str) -> Optional[Dict[str, Any]]:
    """Load an image from file path or URL and return as base64 content block."""
    try:
        if image_path_or_url.startswith(('http://', 'https://')):
            response = httpx.get(image_path_or_url, timeout=30)
            response.raise_for_status()
            image_data = response.content

            content_type = response.headers.get('content-type', 'image/png')
            if 'jpeg' in content_type or 'jpg' in content_type:
                media_type = 'image/jpeg'
            elif 'png' in content_type:
                media_type = 'image/png'
            elif 'gif' in content_type:
                media_type = 'image/gif'
            elif 'webp' in content_type:
                media_type = 'image/webp'
            else:
                media_type = 'image/png'
        else:
            path = Path(image_path_or_url)
            if not path.exists():
                return None

            image_data = path.read_bytes()
            suffix = path.suffix.lower()
            media_types = {
                '.jpg': 'image/jpeg', '.jpeg': 'image/jpeg',
                '.png': 'image/png', '.gif': 'image/gif', '.webp': 'image/webp',
            }
            media_type = media_types.get(suffix, 'image/png')

        b64_data = base64.standard_b64encode(image_data).decode('utf-8')

        return {
            "type": "image",
            "source": {
                "type": "base64",
                "media_type": media_type,
                "data": b64_data,
            }
        }
    except Exception as e:
        logger.warning(f"Could not load image {image_path_or_url}: {e}")
        return None


def _parse_evaluation_response(response_text: str) -> Dict[str, Any]:
    """Parse Claude's evaluation response into structured data."""
    text = response_text.strip()

    # Try direct JSON parse
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    # Look for JSON in markdown blocks
    for marker in ["```json", "```"]:
        if marker in text:
            start = text.find(marker) + len(marker)
            end = text.find("```", start)
            if end > start:
                try:
                    return json.loads(text[start:end].strip())
                except json.JSONDecodeError:
                    pass

    # Look for { ... } pattern
    brace_start = text.find("{")
    brace_end = text.rfind("}") + 1
    if brace_start >= 0 and brace_end > brace_start:
        try:
            return json.loads(text[brace_start:brace_end])
        except json.JSONDecodeError:
            pass

    raise ValueError(f"Could not parse JSON from response: {text[:500]}")


def _extract_dimension_score(
    dimensions: Dict[str, Any],
    name: str,
    default_reasoning: str = "Not evaluated"
) -> DimensionScore:
    """Extract a dimension score from parsed response."""
    dim_data = dimensions.get(name, {})

    if not dim_data:
        return DimensionScore(score=1.0, reasoning=default_reasoning, issues=[])

    # Enforce binary scoring
    raw_score = dim_data.get("score", 1.0)
    score = 1.0 if raw_score >= 0.5 else 0.0

    return DimensionScore(
        score=score,
        reasoning=dim_data.get("reasoning", default_reasoning),
        issues=dim_data.get("issues", [])
    )


def evaluate_question(
    question_dict: Dict[str, Any],
    request: Optional[EvaluationRequest] = None,
    question_type: str = "mcq",
    difficulty: str = "medium",
    curriculum_info: str = "",
    skip_hard_fails: bool = False,
    include_images: bool = True,
) -> BenchmarkResult:
    """
    Evaluate a single question using Claude.

    The evaluation is curriculum-aware and request-centric:
    - If request is provided, it's the ground truth
    - Curriculum context is built dynamically
    - Confidence level affects evaluation strictness

    Args:
        question_dict: Question data dictionary
        request: Original generation request (ground truth)
        question_type: Type of question
        difficulty: Stated difficulty level
        curriculum_info: Deprecated - use request instead
        skip_hard_fails: Skip pre-evaluation checks
        include_images: Include images in evaluation

    Returns:
        BenchmarkResult with all dimension scores
    """
    # Build request from available data if not provided
    if request is None:
        request = EvaluationRequest(
            substandard_id=question_dict.get('substandard_id', curriculum_info or 'UNKNOWN'),
            node_id=question_dict.get('node_id'),
            substandard_description=question_dict.get('substandard_description', ''),
            difficulty=question_dict.get('difficulty', difficulty),
            question_type=question_dict.get('type', question_type),
            lesson_title=question_dict.get('lesson_title', ''),
            instructions=question_dict.get('instructions', ''),
        )

    actual_type = request.question_type
    question_hash = hash_question_dict(question_dict)

    # Check hard fails first
    hard_fail_result = None
    if not skip_hard_fails:
        hard_fail_result = check_hard_fails(question_dict, actual_type)
        if hard_fail_result.failed:
            return _create_hard_fail_result(
                question_hash=question_hash,
                question_type=actual_type,
                hard_fail=hard_fail_result
            )

    # Build DYNAMIC curriculum context (like InceptBench)
    # Uses MongoDB when node_id is available for enriched curriculum facts
    curriculum_context, confidence = build_curriculum_context(
        substandard_id=request.substandard_id,
        node_id=request.node_id,
        substandard_description=request.substandard_description,
        lesson_title=request.lesson_title,
        difficulty=request.difficulty,
        question_type=request.question_type,
        instructions=request.instructions,
    )

    logger.info(f"Evaluating with confidence level: {confidence.level} ({confidence.source})")

    # Format question content
    question_content = format_question_content(question_dict, actual_type)
    type_additions = TYPE_ADDITIONS.get(actual_type, "")

    # Check for images
    image_urls = question_dict.get('image_url', [])
    if isinstance(image_urls, str):
        image_urls = [image_urls] if image_urls else []
    has_images = bool(image_urls) and include_images

    # Build complete prompt with dynamic curriculum context
    prompt = get_evaluation_prompt(
        curriculum_context=curriculum_context,
        question_content=question_content,
        type_specific_additions=type_additions,
        has_images=has_images,
    )

    # Build message content
    content: List[Dict[str, Any]] = []

    # Add images if present
    if has_images:
        for img_url in image_urls:
            img_block = _load_image_as_base64(img_url)
            if img_block:
                content.append(img_block)
                logger.info(f"Added image to evaluation: {img_url[:50]}...")

    # Add text prompt
    content.append({"type": "text", "text": prompt})

    # Call Claude with temperature=0.0 for deterministic results
    client = get_client()
    response = client.messages.create(
        model=EVAL_MODEL,
        max_tokens=3000,
        temperature=0.0,  # Deterministic!
        messages=[{"role": "user", "content": content}]
    )

    # Parse response
    response_text = response.content[0].text
    parsed = _parse_evaluation_response(response_text)

    # Extract issues
    issues = []
    for issue_data in parsed.get("issues", []):
        issues.append(Issue(
            id=issue_data.get("id", "UNKNOWN"),
            dimension=issue_data.get("dimension", "unknown"),
            snippet=issue_data.get("snippet", ""),
            explanation=issue_data.get("explanation", ""),
            severity=issue_data.get("severity", "major")
        ))

    # Extract dimension scores
    dimensions = parsed.get("dimensions", {})

    factual_accuracy = _extract_dimension_score(dimensions, "factual_accuracy")
    curriculum_alignment = _extract_dimension_score(dimensions, "curriculum_alignment")
    cognitive_demand = _extract_dimension_score(dimensions, "cognitive_demand")
    distractor_quality = _extract_dimension_score(dimensions, "distractor_quality")
    explanation_quality = _extract_dimension_score(dimensions, "explanation_quality")
    clarity = _extract_dimension_score(dimensions, "clarity")
    difficulty_alignment = _extract_dimension_score(dimensions, "difficulty_alignment")

    # Count failures for deterministic scoring
    critical_failures = 0
    if factual_accuracy.score == 0.0:
        critical_failures += 1
    if curriculum_alignment.score == 0.0:
        critical_failures += 1

    non_critical_failures = 0
    for dim in [cognitive_demand, distractor_quality, explanation_quality, clarity, difficulty_alignment]:
        if dim.score == 0.0:
            non_critical_failures += 1

    overall_score = calculate_overall_score(critical_failures, non_critical_failures)

    return BenchmarkResult(
        question_hash=question_hash,
        question_type=QuestionType(actual_type) if actual_type in [e.value for e in QuestionType] else QuestionType.MCQ,
        prompt_version=PROMPT_VERSION,
        hard_fail=hard_fail_result,
        issues=issues,
        factual_accuracy=factual_accuracy,
        curriculum_alignment=curriculum_alignment,
        cognitive_demand=cognitive_demand,
        distractor_quality=distractor_quality,
        explanation_quality=explanation_quality,
        clarity=clarity,
        difficulty_alignment=difficulty_alignment,
        overall_score=overall_score,
    )


def _create_hard_fail_result(
    question_hash: str,
    question_type: str,
    hard_fail: HardFailResult
) -> BenchmarkResult:
    """Create a BenchmarkResult for a hard fail (no API call)."""
    fail_score = DimensionScore(
        score=0.0,
        reasoning=f"Hard fail: {', '.join(hard_fail.rules_triggered)}",
        issues=[]
    )

    return BenchmarkResult(
        question_hash=question_hash,
        question_type=QuestionType(question_type) if question_type in [e.value for e in QuestionType] else QuestionType.MCQ,
        prompt_version=PROMPT_VERSION,
        hard_fail=hard_fail,
        issues=[],
        factual_accuracy=fail_score,
        curriculum_alignment=fail_score,
        cognitive_demand=fail_score,
        distractor_quality=fail_score,
        explanation_quality=fail_score,
        clarity=fail_score,
        difficulty_alignment=fail_score,
        overall_score=0.0,
    )


def evaluate_with_request(
    question_dict: Dict[str, Any],
    request_dict: Dict[str, Any],
) -> BenchmarkResult:
    """
    Evaluate a question against an explicit request.

    This is the primary interface - always evaluate against a request.
    """
    skills = request_dict.get('skills', {})
    if isinstance(skills, dict):
        substandard_id = skills.get('substandard_id', 'UNKNOWN')
        substandard_description = skills.get('substandard_description', '')
        lesson_title = skills.get('lesson_title', '')
    else:
        substandard_id = 'UNKNOWN'
        substandard_description = ''
        lesson_title = ''

    # Extract node_id from request_dict or question_dict
    node_id = request_dict.get('node_id') or question_dict.get('node_id')

    request = EvaluationRequest(
        substandard_id=substandard_id,
        node_id=node_id,
        substandard_description=substandard_description,
        difficulty=request_dict.get('difficulty', 'medium'),
        question_type=request_dict.get('type', 'mcq'),
        lesson_title=lesson_title,
        instructions=request_dict.get('instructions', ''),
    )

    return evaluate_question(question_dict=question_dict, request=request)


def evaluate_batch(
    questions: List[Dict[str, Any]],
    requests: Optional[List[Dict[str, Any]]] = None,
    question_type: str = "mcq",
    difficulty: str = "medium",
    curriculum_info: str = "",
    progress_callback: Optional[callable] = None,
) -> Dict[str, BenchmarkResult]:
    """Evaluate a batch of questions."""
    results = {}
    total = len(questions)

    for i, question in enumerate(questions):
        question_id = question.get("id", f"q_{i}")

        request_dict = None
        if requests and i < len(requests):
            request_dict = requests[i]
        elif 'request' in question:
            request_dict = question['request']

        try:
            if request_dict:
                result = evaluate_with_request(question, request_dict)
            else:
                result = evaluate_question(
                    question_dict=question,
                    question_type=question.get("type", question_type),
                    difficulty=question.get("difficulty", difficulty),
                    curriculum_info=question.get("curriculum_info", curriculum_info),
                )
            results[question_id] = result
        except Exception as e:
            logger.error(f"Error evaluating {question_id}: {e}")
            error_score = DimensionScore(score=0.0, reasoning=f"Evaluation error: {str(e)}", issues=[])
            results[question_id] = BenchmarkResult(
                question_hash="error",
                question_type=QuestionType.MCQ,
                prompt_version=PROMPT_VERSION,
                issues=[],
                factual_accuracy=error_score,
                curriculum_alignment=error_score,
                cognitive_demand=error_score,
                distractor_quality=error_score,
                explanation_quality=error_score,
                clarity=error_score,
                difficulty_alignment=error_score,
                overall_score=0.0,
            )

        if progress_callback:
            progress_callback(i + 1, total)

    return results
