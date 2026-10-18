# Spec Delta

## Purpose

Accepts RAG evaluation cases with caller-supplied answers and retrieved contexts, and returns an exact-match score when an expected answer is present.

## ADDED Requirements

### Requirement: RAG evaluation endpoint
The service MUST accept `POST /apis/endpoints/rag/evaluations` with a JSON body containing a non-empty `cases` array. Each case MUST include a non-empty string `id`, a string `question`, a string `answer`, and a `contexts` array. Each context MUST include a non-empty string `id` and a string `text`. A case MAY include a string `expected_answer` and a `relevant_context_ids` array of strings. Case ids in one request MUST be unique. `contexts` MAY be empty.

#### Scenario: Valid RAG case is accepted
- **WHEN** a client posts one case with `id` `r1`, a `question`, an `answer`, and one context with `id` and `text`
- **THEN** the response status is 200 and the body `use_case` is `rag`

### Requirement: RAG request validation
The service MUST reject a RAG evaluation request with HTTP 422 and MUST NOT return a run record when the JSON is malformed, `cases` is missing or empty, a case omits `id`, `question`, `answer`, or `contexts`, a context omits `id` or `text`, a case id is duplicated, or the body contains a field the contract does not define.

#### Scenario: Context missing text is rejected
- **WHEN** a client posts a RAG case whose context omits `text`
- **THEN** the response status is 422 and the body does not contain `run_id`

### Requirement: RAG exact match
When a RAG case includes `expected_answer`, the service MUST score that case with a score named `exact_match`. `passed` and `value` MUST be true only when `answer` and `expected_answer` are identical, including case and whitespace. The service MUST ignore `contexts` and `relevant_context_ids` when computing `exact_match`, and MUST compute that score only from the case fields.

#### Scenario: Identical answer passes
- **WHEN** a RAG case has `answer` `Paris` and `expected_answer` `Paris`
- **THEN** that case's `exact_match` score has `passed` true and `value` true

#### Scenario: Retrieved ids do not change the score
- **WHEN** a RAG case has `answer` equal to `expected_answer` and `relevant_context_ids` that do not match the context ids
- **THEN** that case's `exact_match` score has `passed` true

### Requirement: Unscored RAG case
When a RAG case omits `expected_answer`, the service MUST accept the case and return it with an empty `scores` array.

#### Scenario: Omitted expected answer
- **WHEN** a RAG case includes `answer` and `contexts` and omits `expected_answer`
- **THEN** the response status is 200 and that case's `scores` array is empty

### Requirement: RAG run record
A successful RAG evaluation MUST return a non-empty `run_id`, `use_case` `rag`, one result per case with that case's `case_id`, and a `summary`. `summary.case_count` MUST equal the number of cases. `summary.scored_count` MUST equal the number of cases that included `expected_answer`. `summary.passed_count` MUST equal the number of those scores with `passed` true. Two successful requests MUST receive different `run_id` values.

#### Scenario: Summary counts mixed cases
- **WHEN** a client posts two RAG cases and only the first includes an `expected_answer` that matches its `answer`
- **THEN** `summary.case_count` is 2, `summary.scored_count` is 1, and `summary.passed_count` is 1
