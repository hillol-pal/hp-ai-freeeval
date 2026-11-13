"""Run one prompt and answer through a caller-supplied list of metrics."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from freeeval.metrics.base import RootMetric
from freeeval.metrics.prompt.answer_relevancy import AnswerRelevancy
from freeeval.metrics.prompt.conciseness import Conciseness
from freeeval.metrics.prompt.specificity import Specificity

PROMPT_METRIC_TYPES: dict[str, type[RootMetric]] = {
    "answer_relevancy": AnswerRelevancy,
    "conciseness": Conciseness,
    "specificity": Specificity,
}

Verdict = Literal["pass", "fail"]


@dataclass(frozen=True)
class MetricVerdict:
    name: str
    result: Verdict
    reasoning: str


class PromptEvaluation:
    """Evaluate a prompt and answer with each metric's own threshold."""

    def __init__(self, metrics: list[RootMetric]) -> None:
        self.metrics = metrics

    def evaluate(self, prompt: str, answer: str) -> list[MetricVerdict]:
        verdicts: list[MetricVerdict] = []
        for metric in self.metrics:
            score = float(metric.evaluate(prompt, answer))
            reasoning = getattr(metric, "reasoning", "") or (
                f"Score {score:.2f} compared with threshold {metric.threshold:.2f}."
            )
            verdicts.append(
                MetricVerdict(
                    name=metric.name,
                    result="pass" if score >= metric.threshold else "fail",
                    reasoning=reasoning,
                )
            )
        return verdicts


def build_prompt_metric(name: str, threshold: float) -> RootMetric:
    return PROMPT_METRIC_TYPES[name](threshold)
