from uuid import uuid4

from fastapi import APIRouter

from freeeval.api.schemas import (
    APIError,
    RagEvaluationRequest,
    RagEvaluationResponse,
    RagMetricResult,
)
from freeeval.metrics.rag import RagEvaluation, build_rag_metric

router = APIRouter(prefix="/rag", tags=["rag"])


@router.post(
    "/evaluations",
    response_model=RagEvaluationResponse,
    responses={422: {"model": list[APIError]}},
)
def evaluate_rag(body: RagEvaluationRequest) -> RagEvaluationResponse:
    evaluation = RagEvaluation(
        [build_rag_metric(metric.name, metric.threshold) for metric in body.metrics]
    )
    return RagEvaluationResponse(
        run_id=uuid4().hex,
        metrics=[
            RagMetricResult(name=verdict.name, result=verdict.result, reasoning=verdict.reasoning)
            for verdict in evaluation.evaluate(
                body.query,
                body.actual_response,
                body.retrieved_contexts,
            )
        ],
    )
