"""Shared checks for metrics that score a count out of a total."""


def unit_rate(numerator: int, denominator: int, *, label: str) -> float:
    if denominator <= 0:
        raise ValueError(f"{label} total must be positive")
    if numerator < 0 or numerator > denominator:
        raise ValueError(f"{label} count must be between 0 and total")
    return numerator / denominator
