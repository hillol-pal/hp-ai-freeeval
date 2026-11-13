from uuid import uuid4

from fastapi import APIRouter

from freeeval.api.schemas import CaseResult, CodeEvaluationRequest, RunRecord
from freeeval.api.scoring import exact_scores, summarize
from freeeval.tracing import evaluation_span, metric_span

router = APIRouter(prefix="/code", tags=["code"])


@router.post("/evaluations", response_model=RunRecord)
def evaluate_code(body: CodeEvaluationRequest) -> RunRecord:
    run_id = uuid4().hex
    with evaluation_span(
        "freeeval.code",
        run_id=run_id,
        use_case="code",
        framework="freeeval",
        payload=body.model_dump(),
    ) as trace:
        results: list[CaseResult] = []
        for case in body.cases:
            with metric_span("exact_match", framework="freeeval") as metric:
                scores = exact_scores(case.output, case.expected)
                if scores and scores[0].passed is not None:
                    result = "pass" if scores[0].passed else "fail"
                else:
                    result = "skipped"
                metric.annotate(case_id=case.id, result=result, implementation="freeeval")
                results.append(CaseResult(case_id=case.id, scores=scores))
        record = RunRecord(
            run_id=run_id,
            use_case="code",
            results=results,
            summary=summarize(results),
        )
        trace.set_output(record.model_dump())
        return record
