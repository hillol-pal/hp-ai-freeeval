from fastapi import APIRouter

from freeeval.api.schemas import APIError, PromptEvaluationRequest, PromptMetricResult
from freeeval.metrics.prompt import PromptEvaluation, build_prompt_metric

router = APIRouter(prefix="/prompts", tags=["prompts"])


@router.post(
    "/evaluations",
    response_model=list[PromptMetricResult],
    responses={422: {"model": list[APIError]}},
)
def evaluate_prompts(body: PromptEvaluationRequest) -> list[PromptMetricResult]:
    evaluation = PromptEvaluation(
        [build_prompt_metric(metric.name, metric.threshold) for metric in body.metrics]
    )
    return [
        PromptMetricResult(name=verdict.name, result=verdict.result, reasoning=verdict.reasoning)
        for verdict in evaluation.evaluate(body.prompt, body.answer)
    ]
