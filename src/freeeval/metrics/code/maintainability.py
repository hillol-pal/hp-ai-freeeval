"""How easy the generated code is to change without spreading breakage."""

from __future__ import annotations

from typing import Any

from freeeval.metrics.base import RootMetric
from freeeval.metrics.code.structure import FunctionInfo, module_functions, parse_tree


def _function_score(function: FunctionInfo) -> float:
    depth_score = 1.0 if function.nesting <= 2 else max(0.0, 1 - (function.nesting - 2) / 4)
    length_score = 1.0 if function.line_count <= 30 else max(0.0, 1 - (function.line_count - 30) / 70)
    branch_score = 1.0 if function.branches <= 6 else max(0.0, 1 - (function.branches - 6) / 10)
    return (depth_score + length_score + branch_score) / 3


class Maintainability(RootMetric):
    """Mean of nesting, length, and branch scores for each function.

    A function scores 1 when its nesting is at most 2, its body is at most 30
    lines, and it has at most 6 branches. Code that does not parse, or that
    defines no function, scores 0.
    """

    def __init__(self, threshold: float) -> None:
        super().__init__(name="maintainability", threshold=threshold)
        self.reasoning = ""

    def evaluate(self, code: str, *args: Any, **kwargs: Any) -> float:
        tree = parse_tree(code)
        if tree is None:
            self.reasoning = "The code does not parse, so its structure cannot be maintained safely."
            return 0.0
        functions = module_functions(tree)
        if not functions:
            self.reasoning = "The code defines no function to maintain."
            return 0.0
        score = sum(_function_score(function) for function in functions) / len(functions)
        self.reasoning = (
            f"Maintainability across {len(functions)} functions is {score:.2f}, "
            "based on nesting, length, and branches."
        )
        return score
