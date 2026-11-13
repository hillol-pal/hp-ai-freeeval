# code-evaluation Specification

## Purpose

Accepts code evaluation cases with caller-supplied outputs and returns an exact-match score when an expected output is present.

## Requirements

### Requirement: Code evaluation endpoint
The service MUST accept `POST /apis/endpoints/code/evaluations` with a JSON body containing a non-empty `cases` array. Each case MUST include a non-empty string `id`, a string `code`, and a string `output`. A case MAY include a string `expected`. Case ids in one request MUST be unique.

#### Scenario: Valid code case is accepted
- **WHEN** a client posts one case with `id` `c1`, a `code` string, and an `output` string
- **THEN** the response status is 200 and the body `use_case` is `code`

### Requirement: Code request validation
The service MUST reject a code evaluation request with HTTP 422 and MUST NOT return a run record when the JSON is malformed, `cases` is missing or empty, a case omits `id`, `code`, or `output`, a case id is duplicated, or the body contains a field the contract does not define.

#### Scenario: Missing output is rejected
- **WHEN** a client posts a code case that omits `output`
- **THEN** the response status is 422 and the body does not contain `run_id`

### Requirement: Code exact match
When a code case includes `expected`, the service MUST score that case with a score named `exact_match`. `passed` and `value` MUST be true only when `output` and `expected` are identical, including case and whitespace. The service MUST ignore `code` when computing `exact_match`, and MUST compute that score only from `output` and `expected`.

#### Scenario: Identical output passes
- **WHEN** a code case has `output` `4` and `expected` `4`
- **THEN** that case's `exact_match` score has `passed` true and `value` true

#### Scenario: Different output fails
- **WHEN** a code case has `output` `4` and `expected` `5`
- **THEN** that case's `exact_match` score has `passed` false and `value` false

#### Scenario: Code snippet does not change the score
- **WHEN** a code case has `output` equal to `expected` and a `code` string that differs from `output`
- **THEN** that case's `exact_match` score has `passed` true

### Requirement: Unscored code case
When a code case omits `expected`, the service MUST accept the case and return it with an empty `scores` array.

#### Scenario: Omitted expected value
- **WHEN** a code case includes `output` and `code` and omits `expected`
- **THEN** the response status is 200 and that case's `scores` array is empty

### Requirement: Code run record
A successful code evaluation MUST return a non-empty `run_id`, `use_case` `code`, one result per case with that case's `case_id`, and a `summary`. `summary.case_count` MUST equal the number of cases. `summary.scored_count` MUST equal the number of cases that included `expected`. `summary.passed_count` MUST equal the number of those scores with `passed` true. Two successful requests MUST receive different `run_id` values.

#### Scenario: Summary counts mixed cases
- **WHEN** a client posts two cases and only the first includes an `expected` value that matches its `output`
- **THEN** `summary.case_count` is 2, `summary.scored_count` is 1, and `summary.passed_count` is 1
