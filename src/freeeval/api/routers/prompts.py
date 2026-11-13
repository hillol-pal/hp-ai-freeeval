from uuid import uuid4

from fastapi import APIRouter
from fastapi.responses import JSONResponse

from freeeval.api.errors import judge_error_response
from freeeval.api.schemas import (
    APIError,
    PromptEvaluationRequest,
    PromptEvaluationResponse,
    PromptMetricResult,
)
from freeeval.evaluation.dispatch import score_prompt
from freeeval.evaluation.errors import EvaluationConfigurationError, EvaluationExecutionError

router = APIRouter(prefix="/prompts", tags=["prompts"])


@router.post(
    "/evaluations",
    response_model=PromptEvaluationResponse,
    responses={
        422: {"model": list[APIError]},
        502: {"model": list[APIError]},
        503: {"model": list[APIError]},
    },
)
def evaluate_prompts(body: PromptEvaluationRequest) -> PromptEvaluationResponse | JSONResponse:
    try:
        scored = score_prompt(body.framework, body.prompt, body.answer, body.metrics)
    except (EvaluationConfigurationError, EvaluationExecutionError) as exc:
        return judge_error_response(exc)
    return PromptEvaluationResponse(
        run_id=uuid4().hex,
        framework=body.framework,
        metrics=[
            PromptMetricResult(
                name=item.name,
                result=item.result,
                reasoning=item.reasoning,
                implementation=item.implementation,
            )
            for item in scored
        ],
    )
