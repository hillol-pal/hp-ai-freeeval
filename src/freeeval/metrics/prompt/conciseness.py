"""Length of the answer compared with the prompt."""

from __future__ import annotations

from typing import Any

from freeeval.metrics.base import RootMetric
from freeeval.metrics.prompt.text import tokens, word_count_label


class Conciseness(RootMetric):
    """1 when the answer is no longer than the prompt, otherwise the length ratio."""

    def __init__(self, threshold: float) -> None:
        super().__init__(name="conciseness", threshold=threshold)
        self.reasoning = ""

    def evaluate(self, prompt: str, answer: str, *args: Any, **kwargs: Any) -> float:
        prompt_words = len(tokens(prompt))
        answer_words = len(tokens(answer))
        if answer_words == 0:
            self.reasoning = "The answer has no words."
            return 0.0
        if prompt_words == 0:
            self.reasoning = "The prompt has no words to compare with the answer length."
            return 0.0
        score = min(1.0, prompt_words / answer_words)
        self.reasoning = (
            f"The answer has {answer_words} {word_count_label(answer_words)} and the prompt "
            f"has {prompt_words} {word_count_label(prompt_words)}."
        )
        return score
