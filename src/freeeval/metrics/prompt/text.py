"""Token helpers shared by prompt metrics."""

from __future__ import annotations

import re

_TOKEN = re.compile(r"[a-z0-9]+")
_STOPWORDS = frozenset(
    """
    a an the of to and or in on for with is are was were be this that it
    what how why who when where
    """.split()
)


def tokens(text: str) -> list[str]:
    return _TOKEN.findall(text.lower())


def content_tokens(text: str) -> list[str]:
    return [token for token in tokens(text) if token not in _STOPWORDS]


def word_count_label(count: int) -> str:
    return "word" if count == 1 else "words"
