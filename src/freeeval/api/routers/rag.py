from uuid import uuid4

from fastapi import APIRouter, HTTPException

from freeeval.api.schemas import CaseResult, RagEvaluationRequest, RunRecord, Score
from freeeval.api.scoring import exact_scores, summarize
from freeeval.evaluation.deepeval import (
    EvaluationConfigurationError,
    EvaluationExecutionError,
    MetricEvaluation,
)
from freeeval.evaluation.factory import get_deepeval_evaluator
from freeeval.logging_config import get_logger

router = APIRouter(prefix="/rag", tags=["rag"])
logger = get_logger("freeeval.rag")


def _metric_score(
    name: str,
    evaluation: MetricEvaluation | None,
    *,
    threshold: float,
) -> Score:
    if evaluation is None:
        return Score(
            name=name,
            value=None,
            passed=None,
            reason="Skipped because no retrieval contexts were supplied.",
        )
    return Score(
        name=name,
        value=evaluation.score,
        passed=evaluation.score >= threshold,
        reason=evaluation.reason,
    )


@router.post("/evaluations", response_model=RunRecord)
def evaluate_rag(body: RagEvaluationRequest) -> RunRecord:
    evaluator = get_deepeval_evaluator()
    results: list[CaseResult] = []

    for case in body.cases:
        try:
            metrics = evaluator.evaluate_rag_case(
                question=case.question,
                answer=case.answer,
                retrieval_context=[context.text for context in case.contexts],
                threshold=case.threshold,
            )
        except EvaluationConfigurationError as exc:
            raise HTTPException(status_code=503, detail=str(exc)) from exc
        except EvaluationExecutionError as exc:
            logger.exception("DeepEval RAG scoring failed for case %s", case.id)
            raise HTTPException(
                status_code=502,
                detail=(
                    "DeepEval could not score this RAG case. "
                    "Check the judge model configuration and try again."
                ),
            ) from exc

        # Keep exact_match for callers that provide a reference answer. The two
        # DeepEval scores are independent of expected_answer and relevant ids.
        scores = exact_scores(case.answer, case.expected_answer)
        scores.extend(
            [
                _metric_score(
                    "faithfulness", metrics["faithfulness"], threshold=case.threshold
                ),
                _metric_score(
                    "answer_relevancy",
                    metrics["answer_relevancy"],
                    threshold=case.threshold,
                ),
            ]
        )
        results.append(CaseResult(case_id=case.id, scores=scores))

    return RunRecord(
        run_id=uuid4().hex,
        use_case="rag",
        results=results,
        summary=summarize(results),
    )
