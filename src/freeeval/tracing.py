"""Export evaluation traces to Arize Phoenix.

Every evaluation opens an OpenTelemetry span. Spans stay in-process until
configure_phoenix() registers a collector. Registration runs when
FREEEVAL_PHOENIX_ENABLED is true, or when PHOENIX_COLLECTOR_ENDPOINT or
PHOENIX_API_KEY is set. register() then reads those Phoenix variables.
"""

from __future__ import annotations

import json
import os
from collections.abc import Iterator
from contextlib import contextmanager
from typing import Any

from opentelemetry import trace
from opentelemetry.trace import Status, StatusCode

from freeeval.logging_config import get_logger

logger = get_logger("freeeval.tracing")

_SPAN_KIND = "openinference.span.kind"
_INPUT_VALUE = "input.value"
_OUTPUT_VALUE = "output.value"
_INPUT_MIME_TYPE = "input.mime_type"
_OUTPUT_MIME_TYPE = "output.mime_type"
_JSON_MIME = "application/json"

_tracer_provider: Any = None
_configured = False


def phoenix_export_enabled() -> bool:
    """Return whether this process should push spans to Phoenix."""
    flag = os.getenv("FREEEVAL_PHOENIX_ENABLED")
    if flag is not None and flag.strip() != "":
        return flag.strip().lower() in {"1", "true", "yes", "on"}
    return bool(os.getenv("PHOENIX_COLLECTOR_ENDPOINT") or os.getenv("PHOENIX_API_KEY"))


def configure_phoenix() -> None:
    """Register the Phoenix exporter once. A missing package does not stop the API."""
    global _configured
    if _configured or not phoenix_export_enabled():
        return
    project_name = os.getenv("PHOENIX_PROJECT_NAME", "freeeval")
    try:
        from phoenix.otel import register

        register(project_name=project_name, auto_instrument=True, verbose=False)
    except Exception:
        logger.exception("Phoenix tracing was not registered.")
        return
    _configured = True
    logger.info("Exporting evaluation traces to Phoenix project %s", project_name)


def set_tracer_provider(provider: Any) -> None:
    """Install a tracer provider. Tests use this to capture spans in memory."""
    global _tracer_provider
    _tracer_provider = provider


class SpanWriter:
    """Sets output and metric attributes on one open span."""

    def __init__(self, span: trace.Span) -> None:
        self._span = span

    def set_output(self, value: Any) -> None:
        self._span.set_attribute(_OUTPUT_VALUE, _json(value))
        self._span.set_attribute(_OUTPUT_MIME_TYPE, _JSON_MIME)

    def annotate(self, **attributes: Any) -> None:
        for key, value in attributes.items():
            if value is None:
                continue
            self._span.set_attribute(f"freeeval.metric.{key}", _attribute(value))


@contextmanager
def evaluation_span(
    name: str,
    *,
    run_id: str,
    use_case: str,
    framework: str | None,
    payload: Any,
) -> Iterator[SpanWriter]:
    """Trace one evaluation request. The span records exceptions and re-raises them."""
    with _tracer().start_as_current_span(name) as span:
        span.set_attribute(_SPAN_KIND, "CHAIN")
        span.set_attribute("freeeval.run_id", run_id)
        span.set_attribute("freeeval.use_case", use_case)
        if framework is not None:
            span.set_attribute("freeeval.framework", framework)
        span.set_attribute(_INPUT_VALUE, _json(payload))
        span.set_attribute(_INPUT_MIME_TYPE, _JSON_MIME)
        try:
            yield SpanWriter(span)
        except Exception as exc:
            _mark_error(span, exc)
            raise


@contextmanager
def metric_span(name: str, *, framework: str) -> Iterator[SpanWriter]:
    """Trace one metric. Judge calls made while this span is current nest under it."""
    with _tracer().start_as_current_span(f"freeeval.metric.{name}") as span:
        span.set_attribute(_SPAN_KIND, "EVALUATOR")
        span.set_attribute("freeeval.metric.name", name)
        span.set_attribute("freeeval.framework", framework)
        try:
            yield SpanWriter(span)
        except Exception as exc:
            _mark_error(span, exc)
            raise


def _tracer() -> trace.Tracer:
    if _tracer_provider is not None:
        return _tracer_provider.get_tracer("freeeval")
    return trace.get_tracer("freeeval")


def _mark_error(span: trace.Span, exc: Exception) -> None:
    span.record_exception(exc)
    span.set_status(Status(StatusCode.ERROR, str(exc)))


def _json(value: Any) -> str:
    return json.dumps(value, default=str, ensure_ascii=False)


def _attribute(value: Any) -> str | int | float | bool:
    if isinstance(value, (str, int, float, bool)):
        return value
    return _json(value)
