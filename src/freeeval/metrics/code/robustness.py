"""Whether generated code defines a path for failure."""

from __future__ import annotations

from typing import Any

from freeeval.metrics.base import RootMetric
from freeeval.metrics.code.structure import module_functions, parse_tree


class Robustness(RootMetric):
    """Share of functions that raise or catch an exception.

    A function handles failure when its body contains try or raise. Code that
    does not parse, or that defines no function, scores 0.
    """

    def __init__(self, threshold: float) -> None:
        super().__init__(name="robustness", threshold=threshold)
        self.reasoning = ""

    def evaluate(self, code: str, *args: Any, **kwargs: Any) -> float:
        tree = parse_tree(code)
        if tree is None:
            self.reasoning = "The code does not parse, so its failure paths cannot be checked."
            return 0.0
        functions = module_functions(tree)
        if not functions:
            self.reasoning = "The code defines no function with a failure path."
            return 0.0
        handled = sum(1 for function in functions if function.handles_failure)
        score = handled / len(functions)
        self.reasoning = f"{handled} of {len(functions)} functions raise or catch an exception."
        return score
