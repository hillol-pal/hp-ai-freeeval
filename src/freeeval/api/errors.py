"""Error list returned by the prompt, RAG, and agent evaluation routes."""

from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from freeeval.api.schemas import APIError
from freeeval.evaluation.errors import EvaluationConfigurationError, EvaluationExecutionError

_REASON_BY_TYPE = {
    "missing": "MISSING_FIELD",
    "extra_forbidden": "UNKNOWN_FIELD",
    "string_too_short": "EMPTY",
    "too_short": "EMPTY",
    "greater_than_equal": "OUT_OF_RANGE",
    "less_than_equal": "OUT_OF_RANGE",
    "string_type": "INVALID_TYPE",
    "float_type": "INVALID_TYPE",
    "float_parsing": "INVALID_TYPE",
    "list_type": "INVALID_TYPE",
    "dict_type": "INVALID_TYPE",
    "int_type": "INVALID_TYPE",
    "json_invalid": "INVALID_JSON",
    "json_type": "INVALID_JSON",
}


def validation_errors(exc: RequestValidationError) -> list[APIError]:
    """Turn one FastAPI validation failure into one error item per problem."""
    items: list[APIError] = []
    for error in exc.errors():
        field = _field(error.get("loc", ()))
        message = str(error.get("msg", "Invalid request."))
        items.append(
            APIError(
                error_code="VALIDATION_ERROR",
                reason_code=_reason_code(str(error.get("type", "")), field, message),
                message=f"{field}: {message}" if field != "body" else message,
            )
        )
    return items


def judge_error_response(exc: EvaluationConfigurationError | EvaluationExecutionError) -> JSONResponse:
    """Return the list error body for a judge that is missing or failed."""
    if isinstance(exc, EvaluationConfigurationError):
        item = APIError(
            error_code="EVALUATION_UNAVAILABLE",
            reason_code="JUDGE_NOT_CONFIGURED",
            message=str(exc),
        )
        status_code = 503
    else:
        item = APIError(
            error_code="EVALUATION_FAILED",
            reason_code="JUDGE_FAILED",
            message=str(exc),
        )
        status_code = 502
    return JSONResponse(status_code=status_code, content=[item.model_dump()])


def _field(loc: tuple[object, ...] | list[object]) -> str:
    parts = [str(part) for part in loc if part != "body"]
    return ".".join(parts) if parts else "body"


def _reason_code(error_type: str, field: str, message: str) -> str:
    if error_type == "literal_error" and field.startswith("metrics"):
        return "UNSUPPORTED_METRIC"
    if error_type == "value_error" and "unique" in message:
        return "DUPLICATE_METRIC"
    return _REASON_BY_TYPE.get(error_type, "INVALID_VALUE")
