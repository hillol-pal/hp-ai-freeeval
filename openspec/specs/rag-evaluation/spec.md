# rag-evaluation Specification

## Purpose

Scores one caller-supplied query, actual response, and retrieved contexts with a list of RAG metrics. Each metric carries its own threshold. The response carries a run id and a list of metric name, pass or fail, and reasoning.

## Requirements

### Requirement: RAG evaluation endpoint
The service MUST accept `POST /apis/endpoints/rag/evaluations` with a JSON body containing a non-empty string `query`, a non-empty string `actual_response`, a `retrieved_contexts` array of non-empty strings, and a non-empty `metrics` array. `retrieved_contexts` MAY be empty. Each metric MUST include a `name` and a `threshold` from 0 to 1 inclusive. `name` MUST be `faithfulness` or `answer_relevancy`. Names in one request MUST be unique. The body MAY include a `metadata` object. The body MUST NOT contain a field the contract does not define.

#### Scenario: Valid RAG evaluation is accepted
- **WHEN** a client posts `query` `capital of France`, `actual_response` `Paris is the capital of France`, one retrieved context `Paris is the capital of France.`, and metrics `faithfulness` and `answer_relevancy` at threshold `0.5`
- **THEN** the response status is 200 and the body `metrics` list has one entry per metric in that order

### Requirement: RAG metric verdict
The response body MUST be a JSON object with `run_id`, `framework`, and `metrics`. `run_id` MUST be a non-empty string. Two successful requests MUST receive different `run_id` values. Each item in `metrics` MUST contain `name`, `result`, `reasoning`, and `implementation`. `result` MUST be `pass` when that metric's score is greater than or equal to its own `threshold`, and `fail` otherwise. `reasoning` MUST explain the score. `metadata` MUST NOT be returned and MUST NOT change the score.

#### Scenario: Supported claims pass faithfulness
- **WHEN** the actual response repeats a claim that appears in a retrieved context and faithfulness is requested at threshold `0.5`
- **THEN** that metric's `result` is `pass`

#### Scenario: A lower threshold passes and a higher threshold fails
- **WHEN** answer relevancy for query `capital of France` and actual response `Berlin` is requested once at threshold `0` and once at threshold `0.5`
- **THEN** the first response metric `result` is `pass` and the second response metric `result` is `fail`

### Requirement: RAG request validation
The service MUST reject an invalid RAG evaluation request with HTTP 422. The body MUST be a JSON list. Each item MUST contain `error_code` `VALIDATION_ERROR`, a `reason_code`, and a `message`. The body MUST NOT contain `run_id`. A missing field uses `reason_code` `MISSING_FIELD`. An unknown field uses `UNKNOWN_FIELD`. A metric name outside the supported set uses `UNSUPPORTED_METRIC`. A repeated metric name uses `DUPLICATE_METRIC`. `metadata` that is not an object uses `INVALID_TYPE`.

#### Scenario: Missing fields are listed
- **WHEN** a client posts an empty JSON object
- **THEN** the response status is 422 and the body lists `query`, `actual_response`, `retrieved_contexts`, and `metrics` as `MISSING_FIELD`

#### Scenario: Unknown metric is rejected
- **WHEN** a client posts a metric named `context_precision`
- **THEN** the response status is 422 and the body contains `reason_code` `UNSUPPORTED_METRIC`

### Requirement: RAG metric inputs
`faithfulness` MUST score the actual response against `retrieved_contexts`. `answer_relevancy` MUST score the query against the actual response. Metrics that need a ground-truth answer or relevance labels MUST NOT be accepted by this route.

#### Scenario: Context precision is not accepted
- **WHEN** a client posts a metric named `context_precision`
- **THEN** the response status is 422

### Requirement: RAG scoring framework
The request MAY include `framework` `freeeval`, `deepeval`, or `ragas`. The default MUST be `freeeval`. `deepeval` and `ragas` MUST score `faithfulness` and `answer_relevancy`. `implementation` MUST name the scorer that ran. A missing judge configuration MUST return HTTP 503 and a list containing `reason_code` `JUDGE_NOT_CONFIGURED`. A judge failure MUST return HTTP 502 and MUST NOT fall back to FreeEval.

#### Scenario: Selected framework is echoed
- **WHEN** a client posts `framework` `ragas` with `faithfulness` and `answer_relevancy`
- **THEN** the response `framework` is `ragas` and both metrics have `implementation` `ragas`
