# service-bootstrap Specification

## Purpose

Starts the FreeEval process from documented environment settings and reports that the process is up.

## Requirements

### Requirement: Environment settings have defaults
The process MUST start when `FREEEVAL_HOST`, `FREEEVAL_PORT`, `FREEEVAL_LOG_LEVEL`, and `FREEEVAL_ENV` are unset. The defaults are host `127.0.0.1`, port `8000`, log level `info`, and environment name `local`.

#### Scenario: Start with no environment file
- **WHEN** the process starts with those four variables unset and no environment file present
- **THEN** the process listens on `127.0.0.1` port `8000`

### Requirement: Environment settings override defaults
The process MUST use `FREEEVAL_HOST`, `FREEEVAL_PORT`, `FREEEVAL_LOG_LEVEL`, and `FREEEVAL_ENV` when they are set.

#### Scenario: Custom port
- **WHEN** `FREEEVAL_PORT` is `9001` and the process starts
- **THEN** the process listens on port `9001`

### Requirement: Invalid port is rejected
The process MUST refuse to start when `FREEEVAL_PORT` is not an integer from 1 to 65535.

#### Scenario: Non-numeric port
- **WHEN** `FREEEVAL_PORT` is `abc`
- **THEN** the process exits without serving requests

### Requirement: Health check
The process MUST expose `GET /health`. A successful check returns HTTP 200 and a JSON object whose `status` field is `ok`. The check does not run an evaluation.

#### Scenario: Healthy process
- **WHEN** a client sends `GET /health` with no request body
- **THEN** the response status is 200 and the JSON body field `status` is `ok`

### Requirement: Operator documentation matches runtime settings
The repository MUST document `FREEEVAL_HOST`, `FREEEVAL_PORT`, `FREEEVAL_LOG_LEVEL`, and `FREEEVAL_ENV`, the default for each, how to start the process, and how to call `GET /health`. The environment example MUST list those same variables and defaults and MUST NOT contain secrets.

#### Scenario: Documented defaults match an unset environment
- **WHEN** an operator reads the environment example and the operator documentation
- **THEN** both name the same four variables and the same defaults the process uses when those variables are unset
