from typing import Literal, Protocol

from fastapi import APIRouter, HTTPException
from pydantic import Field

from freeeval.api.schemas import APIModel, NonEmptyStr
from freeeval.evaluation.deepeval import (
    DeepEvalEvaluator,
    EvaluationConfigurationError,
    EvaluationExecutionError,
    MetricEvaluation,
    UnsupportedMetricError,
)
from freeeval.evaluation.factory import get_deepeval_evaluator
from freeeval.logging_config import get_logger

router = APIRouter()
logger = get_logger("freeeval.prompts")

MetricProvider = Literal["deepeval", "ragas"]
VerdictStatus = Literal["pending", "scored"]


class PromptMetric(APIModel):
    name: NonEmptyStr = Field(
        description=(
            "Metric name. DeepEval supports answer_relevancy, toxicity, and bias; "
            "Ragas is reserved and currently returns pending."
        )
    )
    provider: MetricProvider = Field(
        description="Scoring library. DeepEval is implemented; Ragas remains pending.",
    )


class PromptRequest(APIModel):
    prompt: str = Field(description="Prompt text given to the model.")
    response: str = Field(description="Model response to score.")
    metrics: list[PromptMetric] = Field(
        min_length=1,
        description="One verdict is returned for each requested metric, in request order.",
    )
    temperature: float = Field(
        ge=0,
        le=2,
        description="Temperature used by the judge model, not the evaluated model.",
    )
    threshold: float = Field(
        ge=0,
        le=1,
        description="Score at or above this value passes. Applied to every metric.",
    )


class MetricVerdict(APIModel):
    metric: str
    provider: MetricProvider
    threshold: float
    score: float | None = None
    passed: bool | None = None
    reason: str | None = None
    status: VerdictStatus


class PromptResponse(APIModel):
    verdicts: list[MetricVerdict] = Field(
        description="One verdict for each requested metric, in request order.",
    )


class MetricScorer(Protocol):
    def score(
        self,
        *,
        prompt: str,
        response: str,
        metric: str,
        temperature: float,
        threshold: float,
    ) -> MetricEvaluation | None:
        """Return a metric result, or None when that provider is not available yet."""


class DeepEvalScorer:
    def score(
        self,
        *,
        prompt: str,
        response: str,
        metric: str,
        temperature: float,
        threshold: float,
    ) -> MetricEvaluation:
        return get_deepeval_evaluator().evaluate_prompt_metric(
            prompt=prompt,
            response=response,
            metric_name=metric,
            temperature=temperature,
            threshold=threshold,
        )


class PendingScorer:
    def score(
        self,
        *,
        prompt: str,
        response: str,
        metric: str,
        temperature: float,
        threshold: float,
    ) -> None:
        return None


_SCORERS: dict[MetricProvider, MetricScorer] = {
    "deepeval": DeepEvalScorer(),
    "ragas": PendingScorer(),
}


def _verdict(metric: PromptMetric, body: PromptRequest) -> MetricVerdict:
    if (
        metric.provider == "deepeval"
        and metric.name not in DeepEvalEvaluator.PROMPT_METRICS
    ):
        supported = ", ".join(sorted(DeepEvalEvaluator.PROMPT_METRICS))
        raise HTTPException(
            status_code=422,
            detail=(
                f"Unsupported DeepEval prompt metric '{metric.name}'. "
                f"Supported metrics: {supported}."
            ),
        )
    try:
        evaluation = _SCORERS[metric.provider].score(
            prompt=body.prompt,
            response=body.response,
            metric=metric.name,
            temperature=body.temperature,
            threshold=body.threshold,
        )
    except EvaluationConfigurationError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except UnsupportedMetricError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except EvaluationExecutionError as exc:
        logger.exception("DeepEval prompt scoring failed")
        raise HTTPException(
            status_code=502,
            detail="DeepEval could not score this prompt response. Check the judge model configuration and try again.",
        ) from exc

    if evaluation is None:
        return MetricVerdict(
            metric=metric.name,
            provider=metric.provider,
            threshold=body.threshold,
            score=None,
            passed=None,
            reason="This evaluation provider is not implemented yet.",
            status="pending",
        )

    return MetricVerdict(
        metric=metric.name,
        provider=metric.provider,
        threshold=body.threshold,
        score=evaluation.score,
        passed=evaluation.score >= body.threshold,
        reason=evaluation.reason,
        status="scored",
    )


@router.post(
    "/",
    response_model=PromptResponse,
    summary="Score a prompt response",
    description=(
        "DeepEval supports answer_relevancy, toxicity, and bias. "
        "The Ragas provider is reserved and currently returns pending. "
        "Scoring uses the configured judge model and OPENAI_API_KEY."
    ),
    tags=["prompts"],
)
def evaluate_prompt(body: PromptRequest) -> PromptResponse:
    return PromptResponse(verdicts=[_verdict(metric, body) for metric in body.metrics])
