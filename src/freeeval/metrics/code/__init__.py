"""Code-generation metrics."""

from freeeval.metrics.base import RootMetric
from freeeval.metrics.code.extensibility import Extensibility
from freeeval.metrics.code.maintainability import Maintainability
from freeeval.metrics.code.readability import Readability
from freeeval.metrics.code.robustness import Robustness
from freeeval.metrics.code.secured_code import SecuredCode

CODE_METRICS: dict[str, type[RootMetric]] = {
    "maintainability": Maintainability,
    "readability": Readability,
    "robustness": Robustness,
    "secured_code": SecuredCode,
    "extensibility": Extensibility,
}

__all__ = [
    "CODE_METRICS",
    "Extensibility",
    "Maintainability",
    "Readability",
    "Robustness",
    "SecuredCode",
]
