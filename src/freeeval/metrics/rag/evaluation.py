"""Run one RAG query through a caller-supplied list of metrics."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import Literal

from freeeval.metrics.base import RootMetric
from freeeval.metrics.rag.answer_relevancy import AnswerRelevancy
from freeeval.metrics.rag.faithfulness import Faithfulness

RAG_METRIC_TYPES: dict[str, type[RootMetric]] = {
    "faithfulness": Faithfulness,
    "answer_relevancy": AnswerRelevancy,
}

Verdict = Literal["pass", "fail"]


@dataclass(frozen=True)
class MetricVerdict:
    name: str
    result: Verdict
    reasoning: str


class RagEvaluation:
    """Evaluate one query, response, and retrieved contexts with each metric."""

    def __init__(self, metrics: list[RootMetric]) -> None:
        self.metrics = metrics

    def evaluate(
        self,
        query: str,
        actual_response: str,
        retrieved_contexts: Sequence[str],
    ) -> list[MetricVerdict]:
        verdicts: list[MetricVerdict] = []
        for metric in self.metrics:
            score = float(_score(metric, query, actual_response, retrieved_contexts))
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


def build_rag_metric(name: str, threshold: float) -> RootMetric:
    return RAG_METRIC_TYPES[name](threshold)


def _score(
    metric: RootMetric,
    query: str,
    actual_response: str,
    retrieved_contexts: Sequence[str],
) -> float:
    if isinstance(metric, Faithfulness):
        return metric.evaluate(actual_response, retrieved_contexts)
    if isinstance(metric, AnswerRelevancy):
        return metric.evaluate(query, actual_response)
    raise ValueError(f"Unsupported RAG metric: {metric.name}")
