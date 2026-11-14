"""How easy the generated code is to read."""

from __future__ import annotations

import re
from typing import Any

from freeeval.metrics.base import RootMetric
from freeeval.metrics.code.structure import class_names, module_functions, parse_tree

_SNAKE = re.compile(r"^[a-z_][a-z0-9_]*$")
_PASCAL = re.compile(r"^[A-Z][A-Za-z0-9]*$")
_LINE_LIMIT = 88


class Readability(RootMetric):
    """Mean of short lines, 4-space indents, and conventional names.

    A line is short at 88 characters or fewer. An indent passes when its
    width is a multiple of 4. Python function names should be snake_case and
    class names PascalCase. Code with no lines scores 0.
    """

    def __init__(self, threshold: float) -> None:
        super().__init__(name="readability", threshold=threshold)
        self.reasoning = ""

    def evaluate(self, code: str, *args: Any, **kwargs: Any) -> float:
        lines = [line for line in code.splitlines() if line.strip()]
        if not lines:
            self.reasoning = "The code is empty."
            return 0.0
        short = sum(1 for line in lines if len(line) <= _LINE_LIMIT) / len(lines)
        aligned = sum(1 for line in lines if _indent_width(line) % 4 == 0) / len(lines)
        names = _name_score(code)
        parts = [short, aligned] if names is None else [short, aligned, names]
        score = sum(parts) / len(parts)
        self.reasoning = (
            f"{short:.0%} of lines are within {_LINE_LIMIT} characters and "
            f"{aligned:.0%} use a multiple of 4 spaces."
        )
        return score


def _indent_width(line: str) -> int:
    return len(line) - len(line.lstrip(" "))


def _name_score(code: str) -> float | None:
    tree = parse_tree(code)
    if tree is None:
        return None
    function_names = [function.name for function in module_functions(tree)]
    classes = class_names(tree)
    if not function_names and not classes:
        return None
    good = sum(1 for name in function_names if _SNAKE.match(name))
    good += sum(1 for name in classes if _PASCAL.match(name))
    return good / (len(function_names) + len(classes))
