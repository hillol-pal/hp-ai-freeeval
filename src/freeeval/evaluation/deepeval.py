"""DeepEval-backed metrics.

DeepEval is imported lazily so the HTTP API can still start and expose health/docs
routes before an evaluation is requested. Actual scoring requires an OpenAI API
key and uses DeepEval's supported OpenAI model adapter.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import Any

from freeeval.evaluation.errors import EvaluationConfigurationError, EvaluationExecutionError
from freeeval.metrics.agentic.evaluation import TraceStep

__all__ = [
    "DeepEvalEvaluator",
    "EvaluationConfigurationError",
    "EvaluationExecutionError",
    "MetricEvaluation",
]


@dataclass(frozen=True)
class MetricEvaluation:
    """Normalized result returned by a DeepEval metric."""

    score: float
    reason: str | None = None


class DeepEvalEvaluator:
    """Small adapter around DeepEval's synchronous metric API."""

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

    def score_answer_relevancy(
        self, *, question: str, answer: str, threshold: float
    ) -> MetricEvaluation:
        """Score DeepEval's AnswerRelevancyMetric for one question and answer."""
        sdk = self._load_sdk()
        model = self._create_model(sdk, temperature=0.0)
        test_case = sdk.LLMTestCase(input=question, actual_output=answer)
        metric = self._create_metric(sdk.AnswerRelevancyMetric, model=model, threshold=threshold)
        return self._measure(metric, test_case)

    def score_faithfulness(
        self,
        *,
        question: str,
        answer: str,
        contexts: Sequence[str],
        threshold: float,
    ) -> MetricEvaluation:
        """Score DeepEval's FaithfulnessMetric against the retrieved contexts."""
        sdk = self._load_sdk()
        model = self._create_model(sdk, temperature=0.0)
        test_case = sdk.LLMTestCase(
            input=question,
            actual_output=answer,
            retrieval_context=list(contexts),
        )
        metric = self._create_metric(sdk.FaithfulnessMetric, model=model, threshold=threshold)
        return self._measure(metric, test_case)

    def score_task_completion(
        self,
        *,
        task: str,
        output: str,
        trace: Sequence[TraceStep],
        threshold: float,
    ) -> MetricEvaluation:
        """Score DeepEval's TaskCompletionMetric for one execution trace.

        This is a judge of whether the task was completed. It is not the
        FreeEval rule that checks for a trace error.
        """
        sdk = self._load_sdk()
        model = self._create_model(sdk, temperature=0.0)
        test_case = sdk.LLMTestCase(
            input=task,
            actual_output=output,
            tools_called=_tool_calls(sdk, trace, expected=False),
            comments=_trace_comment(trace),
        )
        metric = self._create_metric(
            sdk.TaskCompletionMetric,
            model=model,
            threshold=threshold,
            task=task,
        )
        return self._measure(metric, test_case)

    def score_tool_correctness(
        self,
        *,
        task: str,
        output: str,
        trace: Sequence[TraceStep],
        threshold: float,
    ) -> MetricEvaluation:
        """Score DeepEval's ToolCorrectnessMetric from the execution trace."""
        sdk = self._load_sdk()
        model = self._create_model(sdk, temperature=0.0)
        test_case = sdk.LLMTestCase(
            input=task,
            actual_output=output,
            tools_called=_tool_calls(sdk, trace, expected=False),
            expected_tools=_tool_calls(sdk, trace, expected=True),
        )
        metric = self._create_metric(
            sdk.ToolCorrectnessMetric,
            model=model,
            threshold=threshold,
            should_exact_match=True,
            should_consider_ordering=True,
        )
        return self._measure(metric, test_case)

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
    def _create_metric(metric_class: Any, *, model: Any, threshold: float, **extra: Any) -> Any:
        try:
            return metric_class(
                threshold=threshold,
                model=model,
                include_reason=True,
                async_mode=False,
                **extra,
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
                FaithfulnessMetric,
                TaskCompletionMetric,
                ToolCorrectnessMetric,
            )
            from deepeval.models import OpenAIModel  # type: ignore[import-not-found]
            from deepeval.test_case import LLMTestCase, ToolCall  # type: ignore[import-not-found]
        except ImportError as exc:
            raise EvaluationConfigurationError(
                "DeepEval is not installed. Install project dependencies with `uv sync`."
            ) from exc

        class SDK:
            pass

        SDK.AnswerRelevancyMetric = AnswerRelevancyMetric
        SDK.FaithfulnessMetric = FaithfulnessMetric
        SDK.TaskCompletionMetric = TaskCompletionMetric
        SDK.ToolCorrectnessMetric = ToolCorrectnessMetric
        SDK.OpenAIModel = OpenAIModel
        SDK.LLMTestCase = LLMTestCase
        SDK.ToolCall = ToolCall
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


def _tool_calls(sdk: Any, trace: Sequence[TraceStep], *, expected: bool) -> list[Any]:
    calls: list[Any] = []
    for step in trace:
        if step.kind != "tool":
            continue
        if expected:
            calls.append(
                sdk.ToolCall(
                    name=step.expected_name or "",
                    input_parameters=step.expected_arguments,
                )
            )
        else:
            calls.append(sdk.ToolCall(name=step.name, input_parameters=step.arguments))
    return calls


def _trace_comment(trace: Sequence[TraceStep]) -> str | None:
    if not trace:
        return None
    parts: list[str] = []
    for step in trace:
        detail = f"{step.kind} {step.name}"
        if step.error:
            detail = f"{detail} error={step.error}"
        parts.append(detail)
    return "; ".join(parts)
