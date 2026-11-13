from uuid import uuid4

from fastapi import APIRouter

from freeeval.api.schemas import (
    APIError,
    AgentEvaluationRequest,
    AgentEvaluationResponse,
    AgentMetricResult,
)
from freeeval.metrics.agentic import AgentEvaluation, TraceStep, build_agent_metric

router = APIRouter(prefix="/agents", tags=["agents"])


@router.post(
    "/evaluations",
    response_model=AgentEvaluationResponse,
    responses={422: {"model": list[APIError]}},
)
def evaluate_agents(body: AgentEvaluationRequest) -> AgentEvaluationResponse:
    evaluation = AgentEvaluation(
        [build_agent_metric(metric.name, metric.threshold) for metric in body.metrics]
    )
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
    return AgentEvaluationResponse(
        run_id=uuid4().hex,
        metrics=[
            AgentMetricResult(name=verdict.name, result=verdict.result, reasoning=verdict.reasoning)
            for verdict in evaluation.evaluate(body.input, body.actual_output, trace)
        ],
    )
