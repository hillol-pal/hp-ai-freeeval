"""Token helpers shared by metric implementations."""

from __future__ import annotations

import re
from collections import Counter

_TOKEN = re.compile(r"[a-z0-9]+")
_STOPWORDS = frozenset(
    """
    a an the of to and or in on for with is are was were be this that it
    what how why who when where
    """.split()
)
_SENTENCE = re.compile(r"[^.!?]+")


def tokens(text: str) -> list[str]:
    return _TOKEN.findall(text.lower())


def content_tokens(text: str) -> list[str]:
    return [token for token in tokens(text) if token not in _STOPWORDS]


def word_count_label(count: int) -> str:
    return "word" if count == 1 else "words"


def sentences(text: str) -> list[str]:
    return [part.strip() for part in _SENTENCE.findall(text) if part.strip()]


def token_f1(actual: str, expected: str) -> float:
    """Multiset token F1. Two empty strings score 1."""
    actual_counts = Counter(tokens(actual))
    expected_counts = Counter(tokens(expected))
    if not actual_counts and not expected_counts:
        return 1.0
    if not actual_counts or not expected_counts:
        return 0.0
    overlap = sum((actual_counts & expected_counts).values())
    precision = overlap / sum(actual_counts.values())
    recall = overlap / sum(expected_counts.values())
    if precision + recall == 0:
        return 0.0
    return 2 * precision * recall / (precision + recall)


def claim_supported(claim: str, context_terms: set[str]) -> bool:
    terms = content_tokens(claim)
    if not terms:
        return False
    covered = sum(1 for term in terms if term in context_terms)
    return covered / len(terms) >= 0.6
