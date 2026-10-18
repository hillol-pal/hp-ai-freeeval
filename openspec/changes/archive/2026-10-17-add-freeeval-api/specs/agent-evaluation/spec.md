# Spec Delta

## Purpose

Accepts agent evaluation cases with caller-supplied final outputs and step trajectories, and returns an exact-match score when an expected output is present.

## ADDED Requirements

### Requirement: Agent evaluation endpoint
The service MUST accept `POST /apis/endpoints/agents/evaluations` with a JSON body containing a non-empty `cases` array. Each case MUST include a non-empty string `id`, a string `task`, a string `output`, and a `steps` array. A case MAY include a string `expected_output`. Case ids in one request MUST be unique. `steps` MAY be empty.

#### Scenario: Valid agent case is accepted
- **WHEN** a client posts one case with `id` `a1`, a `task`, an `output`, and one step whose `kind` is `tool` and whose `name` is `search`
- **THEN** the response status is 200 and the body `use_case` is `agent`

#### Scenario: Empty steps are accepted
- **WHEN** a client posts one agent case whose `steps` array is empty and whose other required fields are present
- **THEN** the response status is 200

### Requirement: Agent step fields
Each step MUST include a `kind` of `model`, `retrieve`, `tool`, or `observe`, and a non-empty string `name`. A step MAY include an object `input`, an object `output`, and a string `error`.

#### Scenario: Optional step fields are accepted
- **WHEN** a client posts an agent step with a valid `kind`, a non-empty `name`, an `input` object, an `output` object, and an `error` string
- **THEN** the response status is 200

### Requirement: Agent request validation
The service MUST reject an agent evaluation request with HTTP 422 and MUST NOT return a run record when the JSON is malformed, `cases` is missing or empty, a case omits `id`, `task`, `output`, or `steps`, a step omits `kind` or `name`, a step `kind` is outside `model`, `retrieve`, `tool`, and `observe`, a case id is duplicated, or the body contains a field the contract does not define.

#### Scenario: Unknown step kind is rejected
- **WHEN** a client posts an agent case whose step `kind` is `browse`
- **THEN** the response status is 422 and the body does not contain `run_id`

### Requirement: Agent exact match
When an agent case includes `expected_output`, the service MUST score that case with a score named `exact_match`. `passed` and `value` MUST be true only when `output` and `expected_output` are identical, including case and whitespace. The service MUST ignore `steps` when computing `exact_match`, and MUST compute that score only from the case fields.

#### Scenario: Identical output passes
- **WHEN** an agent case has `output` `done` and `expected_output` `done`
- **THEN** that case's `exact_match` score has `passed` true and `value` true

#### Scenario: Trajectory does not change the score
- **WHEN** an agent case has `output` equal to `expected_output` and a step whose `error` is non-empty
- **THEN** that case's `exact_match` score has `passed` true

### Requirement: Unscored agent case
When an agent case omits `expected_output`, the service MUST accept the case and return it with an empty `scores` array.

#### Scenario: Omitted expected output
- **WHEN** an agent case includes `output` and `steps` and omits `expected_output`
- **THEN** the response status is 200 and that case's `scores` array is empty

### Requirement: Agent run record
A successful agent evaluation MUST return a non-empty `run_id`, `use_case` `agent`, one result per case with that case's `case_id`, and a `summary`. `summary.case_count` MUST equal the number of cases. `summary.scored_count` MUST equal the number of cases that included `expected_output`. `summary.passed_count` MUST equal the number of those scores with `passed` true. Two successful requests MUST receive different `run_id` values.

#### Scenario: Summary counts mixed cases
- **WHEN** a client posts two agent cases and only the first includes an `expected_output` that matches its `output`
- **THEN** `summary.case_count` is 2, `summary.scored_count` is 1, and `summary.passed_count` is 1
