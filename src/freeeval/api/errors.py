"""Error list returned by the prompt, RAG, and agent evaluation routes."""

from fastapi.exceptions import RequestValidationError

from freeeval.api.schemas import APIError

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


def _field(loc: tuple[object, ...] | list[object]) -> str:
    parts = [str(part) for part in loc if part != "body"]
    return ".".join(parts) if parts else "body"


def _reason_code(error_type: str, field: str, message: str) -> str:
    if error_type == "literal_error" and field.startswith("metrics"):
        return "UNSUPPORTED_METRIC"
    if error_type == "value_error" and "unique" in message:
        return "DUPLICATE_METRIC"
    return _REASON_BY_TYPE.get(error_type, "INVALID_VALUE")
