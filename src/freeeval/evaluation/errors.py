"""Failures while a judge SDK scores a metric."""


class EvaluationConfigurationError(RuntimeError):
    """Raised when the evaluator is not configured to make judge-model calls."""


class EvaluationExecutionError(RuntimeError):
    """Raised when a judge SDK cannot complete a metric measurement."""
