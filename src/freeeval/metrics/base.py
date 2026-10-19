from abc import ABC, abstractmethod


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
        pass

    def __repr__(self) -> str: 
        return f"{self.__class__.__name__}(name={self.name}, threshold={self.threshold})"

    
