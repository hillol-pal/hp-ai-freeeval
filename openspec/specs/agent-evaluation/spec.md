# agent-evaluation Specification

## Purpose

Scores one caller-supplied agent input, actual output, and execution trace with a list of agent metrics. Each metric carries its own threshold. The response carries a run id and a list of metric name, pass or fail, and reasoning.

## Requirements

### Requirement: Agent evaluation endpoint
The service MUST accept `POST /apis/endpoints/agents/evaluations` with a JSON body containing a non-empty string `input`, a non-empty string `actual_output`, an `execution_trace` array, and a non-empty `metrics` array. `execution_trace` MAY be empty. Each trace event MUST include a `kind` of `model`, `retrieve`, `tool`, or `observe`, and a non-empty string `name`. A trace event MAY include an `arguments` object, an `expected_name` string, an `expected_arguments` object, an `output` object, and an `error` string. Each metric MUST include a `name` and a `threshold` from 0 to 1 inclusive. `name` MUST be `task_success_rate` or `tool_call_accuracy`. Names in one request MUST be unique. The body MAY include a `metadata` object. The body MUST NOT contain a field the contract does not define.

#### Scenario: Valid agent evaluation is accepted
- **WHEN** a client posts `input` `Find the capital of France`, `actual_output` `Paris`, one tool trace event named `search` whose expected name and arguments match, and metrics `task_success_rate` and `tool_call_accuracy` at threshold `0.5`
- **THEN** the response status is 200 and the body `metrics` list has one entry per metric in that order

#### Scenario: Empty trace is accepted
- **WHEN** a client posts an agent evaluation whose `execution_trace` array is empty and whose other required fields are present
- **THEN** the response status is 200

### Requirement: Agent metric verdict
The response body MUST be a JSON object with `run_id` and `metrics`. `run_id` MUST be a non-empty string. Two successful requests MUST receive different `run_id` values. Each item in `metrics` MUST contain `name`, `result`, and `reasoning`. `result` MUST be `pass` when that metric's score is greater than or equal to its own `threshold`, and `fail` otherwise. `reasoning` MUST explain the score. `metadata` MUST NOT be returned and MUST NOT change the score.

#### Scenario: A trace error fails task success
- **WHEN** task success is requested at threshold `0.5` and one trace event has a non-empty `error`
- **THEN** that metric's `result` is `fail`

#### Scenario: A matching tool call passes
- **WHEN** tool-call accuracy is requested at threshold `0.5` and the only tool event's name and arguments equal its expected name and arguments
- **THEN** that metric's `result` is `pass`

### Requirement: Agent request validation
The service MUST reject an invalid agent evaluation request with HTTP 422. The body MUST be a JSON list. Each item MUST contain `error_code` `VALIDATION_ERROR`, a `reason_code`, and a `message`. The body MUST NOT contain `run_id`. A missing field uses `reason_code` `MISSING_FIELD`. A metric name outside the supported set uses `UNSUPPORTED_METRIC`. A repeated metric name uses `DUPLICATE_METRIC`. A trace `kind` outside `model`, `retrieve`, `tool`, and `observe` MUST be rejected.

#### Scenario: Missing fields are listed
- **WHEN** a client posts an empty JSON object
- **THEN** the response status is 422 and the body lists `input`, `actual_output`, `execution_trace`, and `metrics` as `MISSING_FIELD`

#### Scenario: Unknown trace kind is rejected
- **WHEN** a client posts a trace event whose `kind` is `browse`
- **THEN** the response status is 422 and the body does not contain `run_id`

#### Scenario: Repeated-trial metric is not accepted
- **WHEN** a client posts a metric named `task_reliability`
- **THEN** the response status is 422 and the body contains `reason_code` `UNSUPPORTED_METRIC`

### Requirement: Agent metric inputs
`task_success_rate` MUST score the single execution as successful only when `actual_output` is non-empty and no trace event has an error. `tool_call_accuracy` MUST compare each `tool` event's name and `arguments` with that event's `expected_name` and `expected_arguments`. `task_reliability` MUST NOT be accepted by this route.

#### Scenario: Task reliability is not accepted
- **WHEN** a client posts a metric named `task_reliability`
- **THEN** the response status is 422
