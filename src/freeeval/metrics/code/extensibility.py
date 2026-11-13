"""Whether generated code is split into units that can be extended."""

from __future__ import annotations

from typing import Any

from freeeval.metrics.base import RootMetric
from freeeval.metrics.code.structure import class_names, module_functions, parse_tree

_FOCUSED_LINE_LIMIT = 25


class Extensibility(RootMetric):
    """Mean of modularity, focused units, and parameters.

    Modularity is 1 when the code defines a function or class. Focus is the
    share of functions at most 25 lines long. Parameters are the share of
    functions that take an argument other than self or cls. Code that does
    not parse scores 0.
    """

    def __init__(self, threshold: float) -> None:
        super().__init__(name="extensibility", threshold=threshold)
        self.reasoning = ""

    def evaluate(self, code: str, *args: Any, **kwargs: Any) -> float:
        tree = parse_tree(code)
        if tree is None:
            self.reasoning = "The code does not parse, so it cannot be extended safely."
            return 0.0
        functions = module_functions(tree)
        modular = 1.0 if functions or class_names(tree) else 0.0
        if functions:
            focused = sum(1 for function in functions if function.line_count <= _FOCUSED_LINE_LIMIT)
            focused /= len(functions)
            parameterized = sum(1 for function in functions if function.arg_count > 0) / len(functions)
        else:
            focused = 0.0
            parameterized = 0.0
        score = (modular + focused + parameterized) / 3
        self.reasoning = (
            f"Extensibility is {score:.2f} from {len(functions)} functions, "
            "their size, and their parameters."
        )
        return score
