"""Factory for configured evaluation providers."""

from freeeval.config import Settings
from freeeval.evaluation.deepeval import DeepEvalEvaluator


def get_deepeval_evaluator() -> DeepEvalEvaluator:
    settings = Settings()
    api_key = (
        settings.openai_api_key.get_secret_value()
        if settings.openai_api_key is not None
        else None
    )
    return DeepEvalEvaluator(
        model_name=settings.deepeval_model,
        api_key=api_key,
    )
