# Tasks

## 1. Central logging module

- [x] 1.1 Add `src/freeeval/logging_config.py` with `get_logger(name)` and `setup_logging(level="INFO", *, log_format=None, handlers=None)` as described in `design.md`. `setup_logging()` resolves a string level with `logging.getLevelNamesMapping()` after stripping and uppercasing, raises `ValueError` for an unknown name, sets that level on the root logger, installs one marked `StreamHandler` using `%(levelname)s:%(name)s:%(message)s` unless `log_format` is passed, and appends each extra handler only when that object is not already installed. A later call updates the level and the stream formatter in place. It must not call `logging.basicConfig` or `dictConfig`, and it must not remove handlers it did not add. Verify `tests/test_logging_config.py`: level `warning` emits a warning record and drops an info record on the `freeeval` logger; two calls at `info` leave a single marked stream handler and one logged message is emitted once; an extra handler receives one record and a second call with the same handler does not attach it again; a custom format that includes the logger name and the message is present in the formatted output; `get_logger("freeeval.api")` at level `warning` emits the warning and drops the info record; an unknown level raises `ValueError`. Each test removes only the marked stream handler and handlers it passed in.

## 2. Process entry

- [x] 2.1 In `src/freeeval/main.py`, replace `logging.getLogger("freeeval")` with `get_logger("freeeval")` and replace `logging.basicConfig(...)` with `setup_logging(level=settings.log_level)` after `Settings()` is built and before the `environment=` record. Pass `log_config=None` to `uvicorn.run`. Leave the invalid-port path unchanged so `Settings()` fails before logging is configured and before `uvicorn.run`. Verify `tests/test_main.py`: with the four `FREEEVAL_*` variables unset and the working directory moved off any `.env` file, `main()` emits `environment=local` on the `freeeval` logger; the existing host, port, and `environment=ci` assertions still pass; a monkeypatch shows `setup_logging` is called with the configured level and `uvicorn.run` receives `log_config=None`; `inspect.getsource` of `main` does not contain `basicConfig`; an invalid port still raises `ValidationError` without calling `uvicorn.run`.

## 3. Integration

- [x] 3.1 Run the full test suite from the repo root and verify it passes. Search `src/freeeval` and verify `logging.basicConfig` and `logging.config.dictConfig` are not called anywhere under that package.

## Workflow follow-up

- Archive the change after implementation and review.
