"""Python structure shared by the code-generation metrics."""

from __future__ import annotations

import ast
from dataclasses import dataclass

_CONTAINERS = (
    ast.If,
    ast.For,
    ast.AsyncFor,
    ast.While,
    ast.With,
    ast.AsyncWith,
    ast.Try,
    ast.Match,
)


@dataclass(frozen=True)
class FunctionInfo:
    name: str
    line_count: int
    arg_count: int
    nesting: int
    branches: int
    handles_failure: bool


def parse_tree(code: str) -> ast.AST | None:
    try:
        return ast.parse(code)
    except SyntaxError:
        return None


def module_functions(tree: ast.AST) -> list[FunctionInfo]:
    found: list[FunctionInfo] = []
    for node in getattr(tree, "body", []):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            found.append(function_info(node))
        elif isinstance(node, ast.ClassDef):
            for item in node.body:
                if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    found.append(function_info(item))
    return found


def class_names(tree: ast.AST) -> list[str]:
    return [node.name for node in getattr(tree, "body", []) if isinstance(node, ast.ClassDef)]


def function_info(node: ast.FunctionDef | ast.AsyncFunctionDef) -> FunctionInfo:
    end = node.end_lineno or node.lineno
    names = [
        arg.arg
        for arg in (*node.args.posonlyargs, *node.args.args, *node.args.kwonlyargs)
        if arg.arg not in {"self", "cls"}
    ]
    return FunctionInfo(
        name=node.name,
        line_count=max(end - node.lineno + 1, 1),
        arg_count=len(names),
        nesting=_max_nesting(node),
        branches=_branches(node),
        handles_failure=any(isinstance(child, (ast.Try, ast.Raise)) for child in ast.walk(node)),
    )


def _max_nesting(node: ast.AST) -> int:
    deepest = 0

    def visit(current: ast.AST, depth: int) -> None:
        nonlocal deepest
        for child in ast.iter_child_nodes(current):
            if isinstance(child, _CONTAINERS):
                deepest = max(deepest, depth + 1)
                visit(child, depth + 1)
            else:
                visit(child, depth)

    visit(node, 0)
    return deepest


def _branches(node: ast.AST) -> int:
    count = 0
    for child in ast.walk(node):
        if isinstance(child, (ast.If, ast.For, ast.AsyncFor, ast.While, ast.ExceptHandler)):
            count += 1
        elif isinstance(child, ast.BoolOp):
            count += max(len(child.values) - 1, 0)
    return count
