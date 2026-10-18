from uuid import uuid4

from fastapi import APIRouter

from freeeval.api.schemas import CaseResult, RagEvaluationRequest, RunRecord
from freeeval.api.scoring import exact_scores, summarize

router = APIRouter(prefix="/apis/endpoints/rag", tags=["rag"])


@router.post("/evaluations", response_model=RunRecord)
def evaluate_rag(body: RagEvaluationRequest) -> RunRecord:
    results = [
        CaseResult(
            case_id=case.id,
            scores=exact_scores(case.answer, case.expected_answer),
        )
        for case in body.cases
    ]
    return RunRecord(
        run_id=uuid4().hex,
        use_case="rag",
        results=results,
        summary=summarize(results),
    )
