from uuid import uuid4

from fastapi import APIRouter
from fastapi.responses import JSONResponse

from freeeval.api.errors import judge_error_response
from freeeval.api.schemas import (
    APIError,
    RagEvaluationRequest,
    RagEvaluationResponse,
    RagMetricResult,
)
from freeeval.evaluation.dispatch import score_rag
from freeeval.evaluation.errors import EvaluationConfigurationError, EvaluationExecutionError

router = APIRouter(prefix="/rag", tags=["rag"])


@router.post(
    "/evaluations",
    response_model=RagEvaluationResponse,
    responses={
        422: {"model": list[APIError]},
        502: {"model": list[APIError]},
        503: {"model": list[APIError]},
    },
)
def evaluate_rag(body: RagEvaluationRequest) -> RagEvaluationResponse | JSONResponse:
    try:
        scored = score_rag(
            body.framework,
            body.query,
            body.actual_response,
            body.retrieved_contexts,
            body.metrics,
        )
    except (EvaluationConfigurationError, EvaluationExecutionError) as exc:
        return judge_error_response(exc)
    return RagEvaluationResponse(
        run_id=uuid4().hex,
        framework=body.framework,
        metrics=[
            RagMetricResult(
                name=item.name,
                result=item.result,
                reasoning=item.reasoning,
                implementation=item.implementation,
            )
            for item in scored
        ],
    )
