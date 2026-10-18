import logging
from collections.abc import Sequence

_STREAM_HANDLER_MARK = "_freeeval_stream"
_DEFAULT_FORMAT = "%(levelname)s:%(name)s:%(message)s"


def get_logger(name: str) -> logging.Logger:
    return logging.getLogger(name)


def setup_logging(
    level: str | int = "INFO",
    *,
    log_format: str | None = None,
    handlers: Sequence[logging.Handler] | None = None,
) -> None:
    resolved = _resolve_level(level)
    root = logging.getLogger()
    root.setLevel(resolved)
    formatter = logging.Formatter(log_format or _DEFAULT_FORMAT)
    stream = _find_stream_handler(root)
    if stream is None:
        stream = logging.StreamHandler()
        setattr(stream, _STREAM_HANDLER_MARK, True)
        root.addHandler(stream)
    stream.setFormatter(formatter)
    for handler in handlers or ():
        if handler not in root.handlers:
            root.addHandler(handler)


def _resolve_level(level: str | int) -> int:
    if isinstance(level, int):
        return level
    normalized = level.strip().upper()
    resolved = logging.getLevelNamesMapping().get(normalized)
    if resolved is None:
        raise ValueError(f"Unknown log level: {level}")
    return resolved


def _find_stream_handler(root: logging.Logger) -> logging.Handler | None:
    for handler in root.handlers:
        if getattr(handler, _STREAM_HANDLER_MARK, False):
            return handler
    return None
