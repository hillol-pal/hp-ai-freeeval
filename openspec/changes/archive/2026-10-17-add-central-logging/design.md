# Design

## Context

See proposal.md for why this change exists. The behavior contract is `specs/process-logging/spec.md`.

Today `src/freeeval/main.py` calls `logging.basicConfig(level=settings.log_level.upper())` after `Settings()` is built, then logs `environment=<name>` on the logger named `freeeval`, then calls `uvicorn.run`. No other module configures or emits logs. `FREEEVAL_LOG_LEVEL` defaults to `info` and is not validated beyond being a string. Tests capture the environment line with `caplog`, which attaches its handler to the root logger.

`logging.basicConfig` returns without changes when the root logger already has handlers, so it cannot update the level, the format, or extra handlers on a later call. Uvicorn's default `log_config` calls `logging.config.dictConfig`, whose default `disable_existing_loggers=True` disables loggers created before the server starts. The environment line is logged before `uvicorn.run`, which is why that line is visible today.

## Goals / Non-Goals

**Goals:**

- One function, `setup_logging()`, owns level, format, the process stream handler, and any extra handlers.
- `main()` and any later entry point call that function instead of `basicConfig` or `dictConfig`.
- Modules that emit logs call `get_logger(name)` from the same module.
- A second `setup_logging()` call updates the level and format in place and does not stack handlers.
- The environment line and the invalid-port failure stay in the same order as today.

**Non-Goals:**

- A file sink, JSON logs, or new environment variables. Those can be added later as arguments or handlers inside `logging_config.py`.
- Rebuilding Uvicorn's colored access formatter.
- Configuring logging at import time.
- Changing evaluation routes, health, or settings fields.

## Decisions

### Module and functions

Add `src/freeeval/logging_config.py` with:

- `get_logger(name: str) -> logging.Logger`, a wrapper around `logging.getLogger(name)`. `main()` uses `get_logger("freeeval")` so the startup record stays on that logger. Later modules pass their logger name, conventionally `freeeval...`.
- `setup_logging(level: str | int = "INFO", *, log_format: str | None = None, handlers: Sequence[logging.Handler] | None = None) -> None`.

`level` accepts the lowercase `Settings.log_level` value. Resolve it with `str.strip().upper()` and `logging.getLevelNamesMapping()` (Python 3.11). An unknown name raises `ValueError`. `main()` does not catch that error. An invalid port still fails inside `Settings()` before `setup_logging()` runs.

The default format is the standard library default, `%(levelname)s:%(name)s:%(message)s`. A caller-supplied `log_format` replaces it on the process stream handler.

### Install handlers on the root logger, and make the call idempotent

`setup_logging()` sets the root logger level and attaches one `StreamHandler` to the root logger. The handler is marked with a private attribute so a later call finds it, updates its formatter, and does not add another. Extra handlers are appended only when that same object is not already in `root.handlers`. Handlers the function did not add, including pytest's capture handler, stay in place.

The `freeeval` logger level stays `NOTSET`, so it inherits the root level. Child loggers returned by `get_logger` inherit the same way. That satisfies the module-logger scenario without a separate handler on each logger.

`basicConfig` is not used. It cannot update an existing configuration, which breaks the repeated-call and extra-handler requirements.

Alternative considered: attach the handler only to the `freeeval` logger and set `propagate=False`. That isolates FreeEval from the root logger, but pytest attaches its capture handler to the root logger at fixture entry, so the existing environment-line test would stop seeing records. It would also hide Uvicorn records unless a second handler were installed. Root-level configuration matches today's `basicConfig` and keeps one stream for process and server logs.

### Keep Uvicorn from replacing the configuration

`main()` calls `uvicorn.run(create_app(), host=..., port=..., log_config=None)`.

With the default `log_config`, Uvicorn applies `dictConfig` after startup and can disable the `freeeval` logger. `log_config=None` skips that. Uvicorn still assigns its own level on `uvicorn.error`, `uvicorn.access`, and `uvicorn.asgi`. Those loggers propagate to the root handler installed by `setup_logging()`.

Alternative considered: deepcopy Uvicorn's `LOGGING_CONFIG`, set `disable_existing_loggers=False`, and add a `freeeval` logger entry. That preserves Uvicorn's colored format, but it leaves a second configuration path in `main()` and duplicates Uvicorn's dict. The central function would no longer be the configuration that survives process start.

Trade-off: access lines use the plain process format instead of Uvicorn's colored formatter. The level of those lines is unchanged.

### Where call sites live

Only `main()` configures logging today. It calls `setup_logging(level=settings.log_level)` after `Settings()` and before the environment record. Later entry points, including `src/freeeval/api/apis/main.py` if it grows a `main()`, call the same function. Feature modules do not add handlers or call `basicConfig` or `dictConfig`.

## Risks / Trade-offs

- [Uvicorn access lines lose the default colored formatter] → Accepted. `log_config=None` is what keeps `setup_logging()` in force after the server starts. A later change can pass a richer formatter into `setup_logging()` without new call sites.
- [Root handler is process-global and leaks across tests] → Tests that call `setup_logging()` remove only the marked stream handler and any handler they passed in. They do not clear handlers they did not add.
- [An unknown `FREEEVAL_LOG_LEVEL` raises `ValueError` from `setup_logging()`] → Same class of failure `basicConfig` raises today. No new validation in `Settings`.
- [A second call that omits `handlers` leaves previously added extra handlers installed] → Intentional. The call updates level and format and does not remove foreign or previously requested handlers.

## Migration Plan

Replace the `basicConfig` call in `main()` with `setup_logging()`, and pass `log_config=None` to `uvicorn.run`. No data migration and no new setting. Rollback is restoring the `basicConfig` call and removing the `log_config` argument.
