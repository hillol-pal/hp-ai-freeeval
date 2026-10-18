import logging

import pytest

from freeeval.logging_config import (
    _STREAM_HANDLER_MARK,
    get_logger,
    setup_logging,
)


class CollectHandler(logging.Handler):
    def __init__(self) -> None:
        super().__init__()
        self.records: list[logging.LogRecord] = []

    def emit(self, record: logging.LogRecord) -> None:
        self.records.append(record)


def _messages(handler: CollectHandler) -> list[str]:
    return [record.getMessage() for record in handler.records]


def _marked_handlers() -> list[logging.Handler]:
    return [
        handler
        for handler in logging.getLogger().handlers
        if getattr(handler, _STREAM_HANDLER_MARK, False)
    ]


@pytest.fixture
def isolated_logging() -> object:
    root = logging.getLogger()
    previous_level = root.level
    previous_handlers = list(root.handlers)
    yield
    for handler in list(root.handlers):
        marked = getattr(handler, _STREAM_HANDLER_MARK, False)
        if marked or handler not in previous_handlers:
            root.removeHandler(handler)
    root.setLevel(previous_level)


def test_warning_level_drops_info_on_freeeval_logger(isolated_logging: object) -> None:
    collector = CollectHandler()
    setup_logging(level="warning", handlers=[collector])
    logger = logging.getLogger("freeeval")
    logger.info("hidden")
    logger.warning("shown")
    assert _messages(collector) == ["shown"]


def test_second_call_keeps_one_stream_handler_and_emits_once(
    isolated_logging: object,
) -> None:
    setup_logging(level="info")
    setup_logging(level="info")
    marked = _marked_handlers()
    assert len(marked) == 1
    seen: list[str] = []
    original_emit = marked[0].emit

    def spy(record: logging.LogRecord) -> None:
        seen.append(record.getMessage())
        original_emit(record)

    marked[0].emit = spy  # type: ignore[method-assign]
    get_logger("freeeval").info("once")
    assert seen == ["once"]


def test_extra_handler_is_attached_once(isolated_logging: object) -> None:
    collector = CollectHandler()
    setup_logging(level="info", handlers=[collector])
    setup_logging(level="info", handlers=[collector])
    assert logging.getLogger().handlers.count(collector) == 1
    get_logger("freeeval").info("ping")
    assert _messages(collector) == ["ping"]


def test_custom_format_includes_logger_name_and_message(isolated_logging: object) -> None:
    setup_logging(level="info", log_format="%(name)s %(message)s")
    marked = _marked_handlers()
    assert len(marked) == 1
    record = logging.LogRecord(
        name="freeeval",
        level=logging.INFO,
        pathname=__file__,
        lineno=1,
        msg="hello",
        args=(),
        exc_info=None,
    )
    formatted = marked[0].format(record)
    assert "freeeval" in formatted
    assert "hello" in formatted


def test_module_logger_honors_warning_level(isolated_logging: object) -> None:
    collector = CollectHandler()
    setup_logging(level="warning", handlers=[collector])
    logger = get_logger("freeeval.api")
    logger.info("hidden")
    logger.warning("shown")
    assert _messages(collector) == ["shown"]


def test_unknown_level_raises_value_error(isolated_logging: object) -> None:
    with pytest.raises(ValueError):
        setup_logging(level="not-a-level")


def test_existing_handler_stays_installed(isolated_logging: object) -> None:
    foreign = CollectHandler()
    logging.getLogger().addHandler(foreign)
    setup_logging(level="info")
    assert foreign in logging.getLogger().handlers
