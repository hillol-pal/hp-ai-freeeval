from abc import ABC, abstractmethod
from typing import Any
import numpy as np



class RootMetric(ABC):
    """
    Base class for all metrics. Initialize with name. Define the behavior of a metric thresholding the score and returning a verdict.
    """

    def __init__(self,name: str, threshold: float):
        self.name = name
        self.threshold = threshold
        if not (0 <= threshold <= 1):
            raise ValueError(f"Threshold must be between 0 and 1, got {threshold}")

    @abstractmethod
    def evaluate(self, *args, **kwargs) -> float:
        """
        Evaluate the metric and return a score between 0 and 1.
        """
        result: dict[str,Any] = {}
        return self._apply_threshold(result)

    def __repr__(self) -> str: 
        return f"{self.__class__.__name__}(name={self.name}, threshold={self.threshold})"

    def _apply_threshold(self, results: dict[str, Any]) -> dict[str, Any]:
        """
        Apply the threshold to the score and return a boolean indicating if the score passes.
        """
        if "score" in results:
            if isinstance(results["score"], float) and np.isnan(results["score"]):
                results["passed"] = False
            else:       
                return results["score"] >= self.threshold
            
        return results
