from uuid import uuid4

from fastapi import APIRouter

from freeeval.api.schemas import AgentEvaluationRequest, CaseResult, RunRecord
from freeeval.api.scoring import exact_scores, summarize

router = APIRouter(prefix="/apis/endpoints/agents", tags=["agents"])


@router.post("/evaluations", response_model=RunRecord)
def evaluate_agents(body: AgentEvaluationRequest) -> RunRecord:
    results = [
        CaseResult(
            case_id=case.id,
            scores=exact_scores(case.output, case.expected_output),
        )
        for case in body.cases
    ]
    return RunRecord(
        run_id=uuid4().hex,
        use_case="agent",
        results=results,
        summary=summarize(results),
    )
