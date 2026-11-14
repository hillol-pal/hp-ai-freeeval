"""Ragas-backed metrics.

Ragas is imported only when a Ragas metric is scored. The judge uses the same
OpenAI key and model name as DeepEval. Answer relevancy also uses an OpenAI
embedding because that Ragas metric compares generated questions with the input.
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import Any

from freeeval.evaluation.deepeval import MetricEvaluation
from freeeval.evaluation.errors import EvaluationConfigurationError, EvaluationExecutionError
from freeeval.metrics.agentic.evaluation import TraceStep


def _allow_ragas_vertex_import() -> None:
    """Let ragas 0.4.3 import after langchain-community dropped ChatVertexAI.

    ragas only uses that class to recognize Vertex models. OpenAI scoring never
    constructs it, so a stand-in class is enough for the import.
    """
    import sys
    import types
    import warnings

    module_name = "langchain_community.chat_models.vertexai"
    if module_name in sys.modules:
        return
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", DeprecationWarning)
        try:
            __import__(module_name)
            return
        except ModuleNotFoundError:
            import langchain_community.chat_models as chat_models

    module = types.ModuleType(module_name)
    module.ChatVertexAI = type("ChatVertexAI", (), {})
    sys.modules[module_name] = module
    chat_models.vertexai = module


class RagasEvaluator:
    """Adapter around the Ragas collections metrics used by the HTTP routes."""

    def __init__(
        self,
        *,
        model_name: str,
        api_key: str | None,
        sdk: Any | None = None,
    ) -> None:
        self.model_name = model_name
        self.api_key = api_key
        self._sdk = sdk

    def score_answer_relevancy(
        self, *, question: str, answer: str, threshold: float
    ) -> MetricEvaluation:
        """Score Ragas AnswerRelevancy. Cosine similarity is clamped to [0, 1]."""
        del threshold
        sdk = self._load_sdk()
        scorer = sdk.AnswerRelevancy(llm=self._llm(sdk), embeddings=self._embeddings(sdk))
        result = self._call(
            scorer.score,
            user_input=question,
            response=answer,
        )
        raw = self._value(result)
        score = min(1.0, max(0.0, raw))
        reason = self._reason(result) or f"score {raw:.2f}"
        if score != raw:
            reason = f"{reason} Clamped from {raw:.2f} into [0, 1]."
        return MetricEvaluation(score=score, reason=reason)

    def score_faithfulness(
        self,
        *,
        question: str,
        answer: str,
        contexts: Sequence[str],
        threshold: float,
    ) -> MetricEvaluation:
        """Score Ragas Faithfulness against the retrieved contexts."""
        del threshold
        sdk = self._load_sdk()
        scorer = sdk.Faithfulness(llm=self._llm(sdk))
        result = self._call(
            scorer.score,
            user_input=question,
            response=answer,
            retrieved_contexts=list(contexts),
        )
        return self._checked(result)

    def score_tool_call_accuracy(
        self,
        *,
        task: str,
        output: str,
        trace: Sequence[TraceStep],
        threshold: float,
    ) -> MetricEvaluation:
        """Score Ragas ToolCallAccuracy from tool steps and their expected calls."""
        del threshold
        sdk = self._load_sdk()
        actual, expected = _tool_messages(sdk, task, output, trace)
        scorer = sdk.ToolCallAccuracy()
        result = self._call(scorer.score, user_input=actual, reference_tool_calls=expected)
        return self._checked(result)

    def score_task_success(
        self,
        *,
        task: str,
        output: str,
        trace: Sequence[TraceStep],
        threshold: float,
    ) -> MetricEvaluation:
        """Score Ragas AgentGoalAccuracyWithoutReference for one execution.

        The judge infers the goal from the conversation. It does not use the
        FreeEval trace-error rule.
        """
        del threshold
        sdk = self._load_sdk()
        messages, _expected = _tool_messages(sdk, task, output, trace)
        scorer = sdk.AgentGoalAccuracyWithoutReference(llm=self._llm(sdk))
        result = self._call(scorer.score, user_input=messages)
        return self._checked(result)

    def _llm(self, sdk: Any) -> Any:
        if not self.api_key:
            raise EvaluationConfigurationError(
                "Ragas scoring requires OPENAI_API_KEY. Add it to .env or export it in the shell."
            )
        try:
            client = sdk.AsyncOpenAI(api_key=self.api_key)
            return sdk.llm_factory(self.model_name, client=client, temperature=0.0)
        except Exception as exc:
            raise EvaluationExecutionError("Ragas could not initialize the judge model.") from exc

    def _embeddings(self, sdk: Any) -> Any:
        if not self.api_key:
            raise EvaluationConfigurationError(
                "Ragas scoring requires OPENAI_API_KEY. Add it to .env or export it in the shell."
            )
        try:
            client = sdk.AsyncOpenAI(api_key=self.api_key)
            return sdk.embedding_factory(
                "openai",
                model="text-embedding-3-small",
                client=client,
            )
        except Exception as exc:
            raise EvaluationExecutionError(
                "Ragas could not initialize the embedding model."
            ) from exc

    def _load_sdk(self) -> Any:
        if self._sdk is not None:
            return self._sdk
        _allow_ragas_vertex_import()
        try:
            from openai import AsyncOpenAI
            from ragas.embeddings.base import embedding_factory
            from ragas.llms import llm_factory
            from ragas.messages import AIMessage, HumanMessage, ToolCall
            from ragas.metrics.collections import (
                AgentGoalAccuracyWithoutReference,
                AnswerRelevancy,
                Faithfulness,
                ToolCallAccuracy,
            )
        except ImportError as exc:
            raise EvaluationConfigurationError(
                "Ragas is not installed. Install project dependencies with `uv sync`."
            ) from exc

        class SDK:
            pass

        SDK.AsyncOpenAI = AsyncOpenAI
        SDK.embedding_factory = staticmethod(embedding_factory)
        SDK.llm_factory = staticmethod(llm_factory)
        SDK.AIMessage = AIMessage
        SDK.HumanMessage = HumanMessage
        SDK.ToolCall = ToolCall
        SDK.AgentGoalAccuracyWithoutReference = AgentGoalAccuracyWithoutReference
        SDK.AnswerRelevancy = AnswerRelevancy
        SDK.Faithfulness = Faithfulness
        SDK.ToolCallAccuracy = ToolCallAccuracy
        self._sdk = SDK
        return SDK

    def _call(self, method: Any, **kwargs: Any) -> Any:
        try:
            return method(**kwargs)
        except Exception as exc:
            raise EvaluationExecutionError("Ragas failed while measuring the metric.") from exc

    def _checked(self, result: Any) -> MetricEvaluation:
        score = self._value(result)
        if not 0.0 <= score <= 1.0:
            raise EvaluationExecutionError(
                f"Ragas returned an invalid score outside [0, 1]: {score}."
            )
        return MetricEvaluation(score=score, reason=self._reason(result))

    @staticmethod
    def _value(result: Any) -> float:
        try:
            return float(result.value)
        except (AttributeError, TypeError, ValueError) as exc:
            raise EvaluationExecutionError("Ragas returned a score that is not a number.") from exc

    @staticmethod
    def _reason(result: Any) -> str | None:
        reason = getattr(result, "reason", None)
        return str(reason) if reason else None


def _tool_messages(
    sdk: Any,
    task: str,
    output: str,
    trace: Sequence[TraceStep],
) -> tuple[list[Any], list[Any]]:
    actual_calls: list[Any] = []
    expected_calls: list[Any] = []
    for step in trace:
        if step.kind != "tool":
            continue
        actual_calls.append(sdk.ToolCall(name=step.name, args=step.arguments or {}))
        expected_calls.append(
            sdk.ToolCall(
                name=step.expected_name or "",
                args=step.expected_arguments or {},
            )
        )
    messages = [
        sdk.HumanMessage(content=task),
        sdk.AIMessage(content=output, tool_calls=actual_calls),
    ]
    return messages, expected_calls
