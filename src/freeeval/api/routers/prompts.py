from uuid import uuid4

from fastapi import APIRouter

from freeeval.api.schemas import (
    APIError,
    PromptEvaluationRequest,
    PromptEvaluationResponse,
    PromptMetricResult,
)
from freeeval.metrics.prompt import PromptEvaluation, build_prompt_metric

router = APIRouter(prefix="/prompts", tags=["prompts"])


@router.post(
    "/evaluations",
    response_model=PromptEvaluationResponse,
    responses={422: {"model": list[APIError]}},
)
def evaluate_prompts(body: PromptEvaluationRequest) -> PromptEvaluationResponse:
    evaluation = PromptEvaluation(
        [build_prompt_metric(metric.name, metric.threshold) for metric in body.metrics]
    )
    return PromptEvaluationResponse(
        run_id=uuid4().hex,
        metrics=[
            PromptMetricResult(name=verdict.name, result=verdict.result, reasoning=verdict.reasoning)
            for verdict in evaluation.evaluate(body.prompt, body.answer)
        ],
    )
