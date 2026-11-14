"""Factory for configured evaluation providers."""

from freeeval.config import Settings
from freeeval.evaluation.deepeval import DeepEvalEvaluator
from freeeval.evaluation.ragas import RagasEvaluator


def _judge_settings() -> tuple[str, str | None]:
    settings = Settings()
    api_key = (
        settings.openai_api_key.get_secret_value()
        if settings.openai_api_key is not None
        else None
    )
    return settings.deepeval_model, api_key


def get_deepeval_evaluator() -> DeepEvalEvaluator:
    model_name, api_key = _judge_settings()
    return DeepEvalEvaluator(model_name=model_name, api_key=api_key)


def get_ragas_evaluator() -> RagasEvaluator:
    model_name, api_key = _judge_settings()
    return RagasEvaluator(model_name=model_name, api_key=api_key)
