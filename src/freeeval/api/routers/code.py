from uuid import uuid4

from fastapi import APIRouter

from freeeval.api.schemas import CaseResult, CodeEvaluationRequest, RunRecord
from freeeval.api.scoring import exact_scores, summarize

router = APIRouter(prefix="/code", tags=["code"])


@router.post("/evaluations", response_model=RunRecord)
def evaluate_code(body: CodeEvaluationRequest) -> RunRecord:
    results = [
        CaseResult(
            case_id=case.id,
            scores=exact_scores(case.output, case.expected),
        )
        for case in body.cases
    ]
    return RunRecord(
        run_id=uuid4().hex,
        use_case="code",
        results=results,
        summary=summarize(results),
    )
