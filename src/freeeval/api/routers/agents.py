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
from freeeval.tracing import evaluation_span

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
    run_id = uuid4().hex
    steps = [
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
        with evaluation_span(
            "freeeval.agent",
            run_id=run_id,
            use_case="agent",
            framework=body.framework,
            payload=body.model_dump(),
        ) as trace:
            scored = score_agent(body.framework, body.input, body.actual_output, steps, body.metrics)
            response = AgentEvaluationResponse(
                run_id=run_id,
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
            trace.set_output(response.model_dump())
            return response
    except (EvaluationConfigurationError, EvaluationExecutionError) as exc:
        return judge_error_response(exc)
