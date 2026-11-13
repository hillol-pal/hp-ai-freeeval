"""RAG metrics and the evaluation that runs a list of them."""

from freeeval.metrics.rag.answer_correctness import AnswerCorrectness
from freeeval.metrics.rag.answer_relevancy import AnswerRelevancy
from freeeval.metrics.rag.context_precision import ContextPrecision
from freeeval.metrics.rag.context_recall import ContextRecall
from freeeval.metrics.rag.evaluation import RAG_METRIC_TYPES, RagEvaluation, build_rag_metric
from freeeval.metrics.rag.faithfulness import Faithfulness

RAG_METRICS: dict[str, type] = {
    "faithfulness": Faithfulness,
    "context_precision": ContextPrecision,
    "context_recall": ContextRecall,
    "answer_relevancy": AnswerRelevancy,
    "answer_correctness": AnswerCorrectness,
}

__all__ = [
    "RAG_METRIC_TYPES",
    "RAG_METRICS",
    "AnswerCorrectness",
    "AnswerRelevancy",
    "ContextPrecision",
    "ContextRecall",
    "Faithfulness",
    "RagEvaluation",
    "build_rag_metric",
]
