
from typing import Any

from freeeval.metrics.base import RootMetric


class Evaluator:
    """ 
    Base class for evaluation metrics.
    """

    def __init__(self, metrics: list[RootMetric]):
        self.metrics = metrics

    def evaluate(self, *args, **kwargs) -> dict[str, dict[str,Any]]:
        """
        Evaluate all metrics and return a dictionary of metric names and their scores.
        """
        results = {}
        for metric in self.metrics:
            score = metric.evaluate(*args, **kwargs)
            results[metric.name] = {
                "score": score,
                "passed": score >= metric.threshold
            }
        return results

    def summarise(self, results: dict[str, dict[str,Any]] | None = None) -> dict[str, Any]:
        """
        Summarise the evaluation results.
        """
        if results is None:
            results = self.evaluate()

        summary = {
            "total_metrics": len(self.metrics),
            "passed_metrics": sum(1 for result in results.values() if result["passed"]),
            "failed_metrics": sum(1 for result in results.values() if not result["passed"]),
        }
        return summary