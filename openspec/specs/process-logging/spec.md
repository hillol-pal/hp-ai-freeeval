# process-logging Specification

## Purpose

Configures FreeEval process logging in one place so every module uses the same level, format, and handlers.

## Requirements

### Requirement: One configuration entry
Process logging MUST be configured through a single function, `setup_logging()`. Modules that configure logging MUST call that function. They MUST NOT call `logging.basicConfig` or `logging.dictConfig`.

#### Scenario: Process start uses the central function
- **WHEN** the process starts with a valid port
- **THEN** logging is configured by `setup_logging()` before the startup environment record is emitted
- **AND** the process entry does not call `logging.basicConfig`

### Requirement: Level follows the documented setting
`setup_logging()` MUST set the process log level from `FREEEVAL_LOG_LEVEL`. When that variable is unset, the level MUST be `info`.

#### Scenario: Default level emits the environment record
- **WHEN** the process starts with `FREEEVAL_LOG_LEVEL` unset and a valid port
- **THEN** the `freeeval` logger emits an info record whose message is `environment=local`

#### Scenario: A higher level suppresses info records
- **WHEN** logging is configured with level `warning` and the `freeeval` logger logs one info record and one warning record
- **THEN** the warning record is emitted and the info record is not

### Requirement: Configuration can be applied again
A second call to `setup_logging()` MUST NOT attach a duplicate of a handler already installed by an earlier call.

#### Scenario: Two calls emit one record
- **WHEN** `setup_logging()` is called twice at level `info` and one info message is logged
- **THEN** that message is emitted once

### Requirement: Modules take loggers from the central module
A module that emits logs MUST obtain its logger from the central logging module. That logger MUST use the level and handlers installed by `setup_logging()`.

#### Scenario: A module logger honors the configured level
- **WHEN** `setup_logging()` is called at level `warning` and a logger obtained for a `freeeval` module logs at info and at warning
- **THEN** the warning record is emitted and the info record is not

### Requirement: Extra handlers and formats attach in one place
`setup_logging()` MUST accept additional handlers and a format string. Feature modules MUST NOT install handlers or formatters themselves. Supplying the same extra handler on a later call MUST NOT attach it twice.

#### Scenario: An extra handler receives the record
- **WHEN** `setup_logging()` is called with an additional handler and one record is logged at the configured level
- **THEN** that handler receives the record once

#### Scenario: The format includes the logger name and message
- **WHEN** `setup_logging()` is called with a format that includes the logger name and the message, and one record is logged
- **THEN** the formatted output contains the logger name and the message
