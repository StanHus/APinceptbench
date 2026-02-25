"""Evaluation prompts for different question types."""

from .base import get_evaluation_prompt, PROMPT_VERSION
from .mcq import MCQ_ADDITIONS
from .msq import MSQ_ADDITIONS
from .fill_in import FILL_IN_ADDITIONS
from .match import MATCH_ADDITIONS
from .article import ARTICLE_ADDITIONS

__all__ = [
    "get_evaluation_prompt",
    "PROMPT_VERSION",
    "MCQ_ADDITIONS",
    "MSQ_ADDITIONS",
    "FILL_IN_ADDITIONS",
    "MATCH_ADDITIONS",
    "ARTICLE_ADDITIONS",
]
