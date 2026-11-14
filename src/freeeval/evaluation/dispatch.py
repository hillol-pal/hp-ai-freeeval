"""Choose DeepEval, Ragas, or FreeEval for each requested metric."""

from __future__ import annotations

from collections.abc import Callable, Sequence
from dataclasses import dataclass
from typing import Literal

from freeeval.evaluation.deepeval import MetricEvaluation
from freeeval.metrics.agentic import AgentEvaluation, TraceStep, build_agent_metric
from freeeval.metrics.prompt import PromptEvaluation, build_prompt_metric
from freeeval.metrics.rag import RagEvaluation, build_rag_metric
from freeeval.tracing import metric_span

FrameworkName = Literal["freeeval", "deepeval", "ragas"]
Verdict = Literal["pass", "fail"]

_PROMPT_SUPPORTED: dict[str, set[str]] = {
    "deepeval": {"answer_relevancy"},
    "ragas": {"answer_relevancy"},
}
_RAG_SUPPORTED: dict[str, set[str]] = {
    "deepeval": {"faithfulness", "answer_relevancy"},
    "ragas": {"faithfulness", "answer_relevancy"},
}
_AGENT_SUPPORTED: dict[str, set[str]] = {
    "deepeval": {"task_success_rate", "tool_call_accuracy"},
    "ragas": {"task_success_rate", "tool_call_accuracy"},
}
_LABELS = {
    ("deepeval", "answer_relevancy"): "DeepEval AnswerRelevancyMetric",
    ("deepeval", "faithfulness"): "DeepEval FaithfulnessMetric",
    ("deepeval", "tool_call_accuracy"): "DeepEval ToolCorrectnessMetric",
    ("deepeval", "task_success_rate"): "DeepEval TaskCompletionMetric",
    ("ragas", "answer_relevancy"): "Ragas AnswerRelevancy",
    ("ragas", "faithfulness"): "Ragas Faithfulness",
    ("ragas", "tool_call_accuracy"): "Ragas ToolCallAccuracy",
    ("ragas", "task_success_rate"): "Ragas AgentGoalAccuracyWithoutReference",
}


@dataclass(frozen=True)
class ScoredMetric:
    name: str
    result: Verdict
    reasoning: str
    implementation: FrameworkName


def score_prompt(
    framework: str,
    prompt: str,
    answer: str,
    metrics: Sequence[object],
) -> list[ScoredMetric]:
    return [
        _score_metric(
            framework,
            _name(metric),
            _threshold(metric),
            _PROMPT_SUPPORTED,
            lambda name, threshold: _one(
                PromptEvaluation([build_prompt_metric(name, threshold)]).evaluate(prompt, answer)
            ),
            lambda name, threshold: _prompt_judge(framework, name, threshold, prompt, answer),
        )
        for metric in metrics
    ]


def score_rag(
    framework: str,
    query: str,
    actual_response: str,
    retrieved_contexts: Sequence[str],
    metrics: Sequence[object],
) -> list[ScoredMetric]:
    contexts = list(retrieved_contexts)
    return [
        _score_metric(
            framework,
            _name(metric),
            _threshold(metric),
            _RAG_SUPPORTED,
            lambda name, threshold: _one(
                RagEvaluation([build_rag_metric(name, threshold)]).evaluate(
                    query, actual_response, contexts
                )
            ),
            lambda name, threshold: _rag_judge(
                framework, name, threshold, query, actual_response, contexts
            ),
        )
        for metric in metrics
    ]


def score_agent(
    framework: str,
    task_input: str,
    actual_output: str,
    trace: Sequence[TraceStep],
    metrics: Sequence[object],
) -> list[ScoredMetric]:
    steps = list(trace)
    return [
        _score_metric(
            framework,
            _name(metric),
            _threshold(metric),
            _AGENT_SUPPORTED,
            lambda name, threshold: _one(
                AgentEvaluation([build_agent_metric(name, threshold)]).evaluate(
                    task_input, actual_output, steps
                )
            ),
            lambda name, threshold: _agent_judge(
                framework, name, threshold, task_input, actual_output, steps
            ),
        )
        for metric in metrics
    ]


def _score_metric(
    framework: str,
    name: str,
    threshold: float,
    supported: dict[str, set[str]],
    freeeval: Callable[[str, float], tuple[str, str]],
    judge: Callable[[str, float], MetricEvaluation],
) -> ScoredMetric:
    with metric_span(name, framework=framework) as trace:
        scored = _score_metric_once(framework, name, threshold, supported, freeeval, judge)
        trace.annotate(
            threshold=threshold,
            result=scored.result,
            implementation=scored.implementation,
            reasoning=scored.reasoning,
        )
        return scored


def _score_metric_once(
    framework: str,
    name: str,
    threshold: float,
    supported: dict[str, set[str]],
    freeeval: Callable[[str, float], tuple[str, str]],
    judge: Callable[[str, float], MetricEvaluation],
) -> ScoredMetric:
    if framework in supported and name in supported[framework]:
        evaluation = judge(name, threshold)
        result: Verdict = "pass" if evaluation.score >= threshold else "fail"
        reason = evaluation.reason or f"score {evaluation.score:.2f}"
        label = _LABELS[(framework, name)]
        return ScoredMetric(
            name=name,
            result=result,
            reasoning=f"{label}: {reason}",
            implementation=framework,  # type: ignore[arg-type]
        )
    verdict_result, reasoning = freeeval(name, threshold)
    if framework != "freeeval":
        reasoning = f"FreeEval {name}: {reasoning}"
    return ScoredMetric(
        name=name,
        result=verdict_result,  # type: ignore[arg-type]
        reasoning=reasoning,
        implementation="freeeval",
    )


def _prompt_judge(framework: str, name: str, threshold: float, prompt: str, answer: str) -> MetricEvaluation:
    if framework == "deepeval":
        return _deepeval().score_answer_relevancy(question=prompt, answer=answer, threshold=threshold)
    elif framework == "ragas":
        return _ragas().score_answer_relevancy(question=prompt, answer=answer, threshold=threshold)


def _rag_judge(
    framework: str,
    name: str,
    threshold: float,
    query: str,
    answer: str,
    contexts: Sequence[str],
) -> MetricEvaluation:
    if name == "faithfulness" and framework == "deepeval":
        return _deepeval().score_faithfulness(
            question=query, answer=answer, contexts=contexts, threshold=threshold
        )
    if name == "faithfulness":
        return _ragas().score_faithfulness(
            question=query, answer=answer, contexts=contexts, threshold=threshold
        )
    if framework == "deepeval":
        return _deepeval().score_answer_relevancy(question=query, answer=answer, threshold=threshold)
    return _ragas().score_answer_relevancy(question=query, answer=answer, threshold=threshold)


def _agent_judge(
    framework: str,
    name: str,
    threshold: float,
    task_input: str,
    actual_output: str,
    trace: Sequence[TraceStep],
) -> MetricEvaluation:
    if name == "tool_call_accuracy" and framework == "deepeval":
        return _deepeval().score_tool_correctness(
            task=task_input, output=actual_output, trace=trace, threshold=threshold
        )
    if name == "tool_call_accuracy":
        return _ragas().score_tool_call_accuracy(
            task=task_input, output=actual_output, trace=trace, threshold=threshold
        )
    if framework == "deepeval":
        return _deepeval().score_task_completion(
            task=task_input, output=actual_output, trace=trace, threshold=threshold
        )
    return _ragas().score_task_success(
        task=task_input, output=actual_output, trace=trace, threshold=threshold
    )


def _deepeval():  # type: ignore[no-untyped-def]
    from freeeval.evaluation.factory import get_deepeval_evaluator

    return get_deepeval_evaluator()


def _ragas():  # type: ignore[no-untyped-def]
    from freeeval.evaluation.factory import get_ragas_evaluator

    return get_ragas_evaluator()


def _one(verdicts: Sequence[object]) -> tuple[str, str]:
    verdict = verdicts[0]
    return str(verdict.result), str(verdict.reasoning)  # type: ignore[attr-defined]


def _name(metric: object) -> str:
    return str(getattr(metric, "name"))


def _threshold(metric: object) -> float:
    return float(getattr(metric, "threshold"))
