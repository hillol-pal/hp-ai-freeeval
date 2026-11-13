from uuid import uuid4

from fastapi import APIRouter

from freeeval.api.schemas import CaseResult, PromptEvaluationRequest, RunRecord
from freeeval.api.scoring import exact_scores, summarize

router = APIRouter(prefix="/prompts", tags=["prompts"])


@router.post("/evaluations", response_model=RunRecord)
def evaluate_prompts(body: PromptEvaluationRequest) -> RunRecord:
    results = [
        CaseResult(
            case_id=case.id,
            scores=exact_scores(case.output, case.expected),
        )
        for case in body.cases
    ]
    return RunRecord(
        run_id=uuid4().hex,
        use_case="prompt",
        results=results,
        summary=summarize(results),
    )
