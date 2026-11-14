"""Deterministic evaluation requests for tests and manual checks.

The samples are fixed. `generate` walks that catalog from `seed` and repeats
when `count` is longer than the catalog. Nothing here calls a model.
"""

from __future__ import annotations

from copy import deepcopy
from typing import Any

from data_generation.agents import samples as agent_samples
from data_generation.code import samples as code_samples
from data_generation.prompts import samples as prompt_samples
from data_generation.rag import samples as rag_samples
from data_generation.sample import Category, Sample, Verdict

_CATALOGS: dict[Category, tuple[Sample, ...]] = {
    "prompt": prompt_samples(),
    "code": code_samples(),
    "rag": rag_samples(),
    "agent": agent_samples(),
}

__all__ = ["Category", "Sample", "Verdict", "catalog", "generate", "generate_all"]


def catalog(category: Category) -> tuple[Sample, ...]:
    """Return every sample for one category, in catalog order."""
    try:
        items = _CATALOGS[category]
    except KeyError as exc:
        raise ValueError(f"Unknown category: {category}") from exc
    return tuple(_copy(sample) for sample in items)


def generate(category: Category, *, count: int = 1, seed: int = 0) -> list[Sample]:
    """Return `count` samples, starting at `seed` modulo the catalog length."""
    if count < 1:
        raise ValueError("count must be at least 1")
    if seed < 0:
        raise ValueError("seed must be at least 0")
    items = catalog(category)
    start = seed % len(items)
    return [items[(start + offset) % len(items)] for offset in range(count)]


def generate_all() -> list[Sample]:
    """Return one copy of every sample, prompt then code, RAG, and agent."""
    return [sample for category in ("prompt", "code", "rag", "agent") for sample in catalog(category)]


def _copy(sample: Sample) -> Sample:
    body: dict[str, Any] = deepcopy(sample.body)
    return Sample(
        category=sample.category,
        name=sample.name,
        body=body,
        expected_results=dict(sample.expected_results),
    )
