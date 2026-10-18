# Spec Delta

## Purpose

Accepts prompt evaluation cases with caller-supplied outputs and returns an exact-match score when an expected output is present.

## ADDED Requirements

### Requirement: Prompt evaluation endpoint
The service MUST accept `POST /apis/endpoints/prompts/evaluations` with a JSON body containing a non-empty `cases` array. Each case MUST include a non-empty string `id`, an object `input`, and a string `output`. A case MAY include a string `expected`. Case ids in one request MUST be unique.

#### Scenario: Valid prompt case is accepted
- **WHEN** a client posts one case with `id` `p1`, an `input` object, and an `output` string
- **THEN** the response status is 200 and the body `use_case` is `prompt`

### Requirement: Prompt request validation
The service MUST reject a prompt evaluation request with HTTP 422 and MUST NOT return a run record when the JSON is malformed, `cases` is missing or empty, a case omits `id`, `input`, or `output`, a case id is duplicated, or the body contains a field the contract does not define.

#### Scenario: Missing output is rejected
- **WHEN** a client posts a prompt case that omits `output`
- **THEN** the response status is 422 and the body does not contain `run_id`

### Requirement: Prompt exact match
When a prompt case includes `expected`, the service MUST score that case with a score named `exact_match`. `passed` and `value` MUST be true only when `output` and `expected` are identical, including case and whitespace. The service MUST compute that score only from the case fields.

#### Scenario: Identical output passes
- **WHEN** a prompt case has `output` `Yes` and `expected` `Yes`
- **THEN** that case's `exact_match` score has `passed` true and `value` true

#### Scenario: Different output fails
- **WHEN** a prompt case has `output` `Yes` and `expected` `No`
- **THEN** that case's `exact_match` score has `passed` false and `value` false

### Requirement: Unscored prompt case
When a prompt case omits `expected`, the service MUST accept the case and return it with an empty `scores` array.

#### Scenario: Omitted expected value
- **WHEN** a prompt case includes `output` and omits `expected`
- **THEN** the response status is 200 and that case's `scores` array is empty

### Requirement: Prompt run record
A successful prompt evaluation MUST return a non-empty `run_id`, `use_case` `prompt`, one result per case with that case's `case_id`, and a `summary`. `summary.case_count` MUST equal the number of cases. `summary.scored_count` MUST equal the number of cases that included `expected`. `summary.passed_count` MUST equal the number of those scores with `passed` true. Two successful requests MUST receive different `run_id` values.

#### Scenario: Summary counts mixed cases
- **WHEN** a client posts two cases and only the first includes an `expected` value that matches its `output`
- **THEN** `summary.case_count` is 2, `summary.scored_count` is 1, and `summary.passed_count` is 1
