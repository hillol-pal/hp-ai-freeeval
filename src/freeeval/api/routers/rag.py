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
from freeeval.tracing import evaluation_span

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
    run_id = uuid4().hex
    try:
        with evaluation_span(
            "freeeval.rag",
            run_id=run_id,
            use_case="rag",
            framework=body.framework,
            payload=body.model_dump(),
        ) as trace:
            scored = score_rag(
                body.framework,
                body.query,
                body.actual_response,
                body.retrieved_contexts,
                body.metrics,
            )
            response = RagEvaluationResponse(
                run_id=run_id,
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
            trace.set_output(response.model_dump())
            return response
    except (EvaluationConfigurationError, EvaluationExecutionError) as exc:
        return judge_error_response(exc)
