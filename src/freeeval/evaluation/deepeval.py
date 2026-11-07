"""DeepEval-backed metrics.

DeepEval is imported lazily so the HTTP API can still start and expose health/docs
routes before an evaluation is requested. Actual scoring requires an OpenAI API
key and uses DeepEval's supported OpenAI model adapter.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


class EvaluationConfigurationError(RuntimeError):
    """Raised when the evaluator is not configured to make judge-model calls."""


class EvaluationExecutionError(RuntimeError):
    """Raised when DeepEval cannot complete a metric measurement."""


class UnsupportedMetricError(ValueError):
    """Raised when a requested metric is not supported by this endpoint."""


@dataclass(frozen=True)
class MetricEvaluation:
    """Normalized result returned by a DeepEval metric."""

    score: float
    reason: str | None = None


class DeepEvalEvaluator:
    """Small adapter around DeepEval's synchronous metric API."""

    PROMPT_METRICS = {
        "answer_relevancy": "AnswerRelevancyMetric",
        "toxicity": "ToxicityMetric",
        "bias": "BiasMetric",
    }

    def __init__(
        self,
        *,
        model_name: str,
        api_key: str | None,
        sdk: Any | None = None,
    ) -> None:
        self.model_name = model_name
        self.api_key = api_key
        # Tests can inject a tiny fake SDK. Production imports DeepEval only on use.
        self._sdk = sdk

    def evaluate_prompt_metric(
        self,
        *,
        prompt: str,
        response: str,
        metric_name: str,
        threshold: float,
        temperature: float,
    ) -> MetricEvaluation:
        metric_class_name = self.PROMPT_METRICS.get(metric_name)
        if metric_class_name is None:
            supported = ", ".join(sorted(self.PROMPT_METRICS))
            raise UnsupportedMetricError(
                f"Unsupported DeepEval prompt metric '{metric_name}'. Supported metrics: {supported}."
            )

        sdk = self._load_sdk()
        model = self._create_model(sdk, temperature=temperature)
        metric_class = getattr(sdk, metric_class_name)
        metric = self._create_metric(metric_class, model=model, threshold=threshold)
        test_case = sdk.LLMTestCase(input=prompt, actual_output=response)
        return self._measure(metric, test_case)

    def evaluate_rag_case(
        self,
        *,
        question: str,
        answer: str,
        retrieval_context: list[str],
        threshold: float,
    ) -> dict[str, MetricEvaluation | None]:
        """Score answer relevancy and, when contexts exist, faithfulness.

        Answer relevancy is referenceless and needs only the question and answer.
        Faithfulness needs at least one retrieved context. For an empty context
        list, the returned faithfulness value is None and the API marks it skipped.
        """
        sdk = self._load_sdk()
        model = self._create_model(sdk, temperature=0.0)
        test_case = sdk.LLMTestCase(
            input=question,
            actual_output=answer,
            retrieval_context=retrieval_context,
        )

        answer_relevancy_metric = self._create_metric(
            sdk.AnswerRelevancyMetric, model=model, threshold=threshold
        )
        answer_relevancy = self._measure(answer_relevancy_metric, test_case)

        faithfulness: MetricEvaluation | None = None
        if retrieval_context:
            faithfulness_metric = self._create_metric(
                sdk.FaithfulnessMetric, model=model, threshold=threshold
            )
            faithfulness = self._measure(faithfulness_metric, test_case)

        return {
            "faithfulness": faithfulness,
            "answer_relevancy": answer_relevancy,
        }

    def _create_model(self, sdk: Any, *, temperature: float) -> Any:
        if not self.api_key:
            raise EvaluationConfigurationError(
                "DeepEval scoring requires OPENAI_API_KEY. Add it to .env or export it in the shell."
            )
        try:
            return sdk.OpenAIModel(
                model=self.model_name,
                api_key=self.api_key,
                temperature=temperature,
            )
        except Exception as exc:
            raise EvaluationExecutionError(
                "DeepEval could not initialize the configured judge model."
            ) from exc

    @staticmethod
    def _create_metric(metric_class: Any, *, model: Any, threshold: float) -> Any:
        try:
            return metric_class(
                threshold=threshold,
                model=model,
                include_reason=True,
                async_mode=False,
            )
        except Exception as exc:
            raise EvaluationExecutionError(
                "DeepEval could not initialize the requested metric."
            ) from exc

    def _load_sdk(self) -> Any:
        if self._sdk is not None:
            return self._sdk
        try:
            from deepeval.metrics import (  # type: ignore[import-not-found]
                AnswerRelevancyMetric,
                BiasMetric,
                FaithfulnessMetric,
                ToxicityMetric,
            )
            from deepeval.models import OpenAIModel  # type: ignore[import-not-found]
            from deepeval.test_case import LLMTestCase  # type: ignore[import-not-found]
        except ImportError as exc:
            raise EvaluationConfigurationError(
                "DeepEval is not installed. Install project dependencies with `uv sync --extra dev`."
            ) from exc

        class SDK:
            pass

        SDK.AnswerRelevancyMetric = AnswerRelevancyMetric
        SDK.BiasMetric = BiasMetric
        SDK.FaithfulnessMetric = FaithfulnessMetric
        SDK.ToxicityMetric = ToxicityMetric
        SDK.OpenAIModel = OpenAIModel
        SDK.LLMTestCase = LLMTestCase
        self._sdk = SDK
        return SDK

    @staticmethod
    def _measure(metric: Any, test_case: Any) -> MetricEvaluation:
        try:
            metric.measure(test_case)
            score = float(metric.score)
        except Exception as exc:  # DeepEval/provider exceptions need an API-safe boundary.
            raise EvaluationExecutionError("DeepEval failed while measuring the metric.") from exc

        if not 0.0 <= score <= 1.0:
            raise EvaluationExecutionError(
                f"DeepEval returned an invalid score outside [0, 1]: {score}."
            )
        reason = getattr(metric, "reason", None)
        return MetricEvaluation(score=score, reason=reason)
