from uuid import uuid4

from fastapi import APIRouter
from fastapi.responses import JSONResponse

from freeeval.api.errors import judge_error_response
from freeeval.api.schemas import (
    APIError,
    AgentEvaluationRequest,
    AgentEvaluationResponse,
    AgentMetricResult,
)
from freeeval.evaluation.dispatch import score_agent
from freeeval.evaluation.errors import EvaluationConfigurationError, EvaluationExecutionError
from freeeval.metrics.agentic import TraceStep

router = APIRouter(prefix="/agents", tags=["agents"])


@router.post(
    "/evaluations",
    response_model=AgentEvaluationResponse,
    responses={
        422: {"model": list[APIError]},
        502: {"model": list[APIError]},
        503: {"model": list[APIError]},
    },
)
def evaluate_agents(body: AgentEvaluationRequest) -> AgentEvaluationResponse | JSONResponse:
    trace = [
        TraceStep(
            kind=event.kind,
            name=event.name,
            arguments=event.arguments,
            expected_name=event.expected_name,
            expected_arguments=event.expected_arguments,
            error=event.error,
        )
        for event in body.execution_trace
    ]
    try:
        scored = score_agent(body.framework, body.input, body.actual_output, trace, body.metrics)
    except (EvaluationConfigurationError, EvaluationExecutionError) as exc:
        return judge_error_response(exc)
    return AgentEvaluationResponse(
        run_id=uuid4().hex,
        framework=body.framework,
        metrics=[
            AgentMetricResult(
                name=item.name,
                result=item.result,
                reasoning=item.reasoning,
                implementation=item.implementation,
            )
            for item in scored
        ],
    )
