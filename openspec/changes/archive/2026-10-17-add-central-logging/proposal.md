# Proposal

## Why

Process logging is configured inline in `src/freeeval/main.py` with `logging.basicConfig`. Every later module that needs a level, format, or handler would copy that call. One `setup_logging()` keeps today's level behavior and gives extra configuration a single place to live.

## What Changes

- Add `src/freeeval/logging_config.py` with `setup_logging()` as the only function that configures process logging.
- Put the basic setup there: level, format, and the stream handler. Put any further logging configuration (extra handlers, formatters, or logger levels) in the same module so call sites stay unchanged.
- Call `setup_logging()` from each place that configures logging. Today that place is `main()` in `src/freeeval/main.py`, which calls `logging.basicConfig` directly. Modules that only emit logs take a logger from this module and do not call `basicConfig` or `dictConfig`.
- Keep the current startup behavior. `FREEEVAL_LOG_LEVEL` still sets the level (default `info`). The process still logs `environment=<name>` on the `freeeval` logger before it serves requests. An invalid port still exits before the server starts.
- Make the setup safe to call more than once so a second entry point does not stack duplicate handlers.
- No new environment variables, HTTP routes, or dependencies. `uvicorn.run` is called with `log_config=None` so Uvicorn's `dictConfig` does not replace this setup. Uvicorn still sets the level on its own loggers.

## Capabilities

### New Capabilities

- `process-logging`: Central, extensible logging configuration for the FreeEval process. `setup_logging()` applies the level and handlers. Modules that need logging configured call that function instead of configuring the standard library themselves.

### Modified Capabilities

- None. `service-bootstrap` still requires the same four settings, the same defaults, the health check, and the same operator documentation. This change does not alter those requirements.

## Impact

- New module: `src/freeeval/logging_config.py`.
- Edited module: `src/freeeval/main.py`, which stops calling `logging.basicConfig` and calls `setup_logging()` with the level from `Settings`.
- Tests cover the applied level, a repeated call that does not duplicate handlers, and the existing `environment=` startup line.
- No HTTP API, dependency, or published environment-variable changes.

Assumption: this change does not add a file sink or JSON logs. Extensibility is the function and module boundary, so a later change can add those inside `logging_config.py` without touching feature modules.
