from typing import Literal, Protocol

from fastapi import APIRouter
from pydantic import Field

from freeeval.api.schemas import APIModel, NonEmptyStr

router = APIRouter()

MetricProvider = Literal["deepeval", "ragas"]
VerdictStatus = Literal["pending", "scored"]


class PromptMetric(APIModel):
    name: NonEmptyStr = Field(description="Metric name for the selected provider.")
    provider: MetricProvider = Field(
        description="Scoring library. DeepEval and Ragas are accepted now and scored by a later runner.",
    )


class PromptRequest(APIModel):
    prompt: str = Field(description="Prompt text given to the model.")
    response: str = Field(description="Model response to score.")
    metrics: list[PromptMetric] = Field(
        min_length=1,
        description="Metrics to judge. One verdict is returned for each entry.",
    )
    temperature: float = Field(ge=0, le=2, description="Sampling temperature for model-based metrics.")
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
    ) -> float | None:
        """Return a score from 0 to 1, or None when this provider is not running yet."""


class PendingScorer:
    def score(
        self,
        *,
        prompt: str,
        response: str,
        metric: str,
        temperature: float,
    ) -> float | None:
        return None


_SCORERS: dict[MetricProvider, MetricScorer] = {
    "deepeval": PendingScorer(),
    "ragas": PendingScorer(),
}


def _verdict(metric: PromptMetric, body: PromptRequest) -> MetricVerdict:
    score = _SCORERS[metric.provider].score(
        prompt=body.prompt,
        response=body.response,
        metric=metric.name,
        temperature=body.temperature,
    )
    if score is None:
        return MetricVerdict(
            metric=metric.name,
            provider=metric.provider,
            threshold=body.threshold,
            score=None,
            passed=None,
            status="pending",
        )
    return MetricVerdict(
        metric=metric.name,
        provider=metric.provider,
        threshold=body.threshold,
        score=score,
        passed=score >= body.threshold,
        status="scored",
    )


@router.post(
    "/",
    response_model=PromptResponse,
    summary="Score a prompt response",
    description=(
        "Returns one verdict for each metric. "
        "DeepEval and Ragas providers are part of the contract and are scored when a runner is registered."
    ),
    tags=["prompts"],
    responses={
        200: {
            "description": "One verdict per requested metric.",
            "model": PromptResponse,
        }
    },
)
async def evaluate_prompt(body: PromptRequest) -> PromptResponse:
    return PromptResponse(verdicts=[_verdict(metric, body) for metric in body.metrics])
