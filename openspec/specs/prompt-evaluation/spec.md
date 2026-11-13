# prompt-evaluation Specification

## Purpose

Scores one caller-supplied prompt and answer with a list of prompt metrics. Each metric carries its own threshold. The response is a list of metric name, pass or fail, and reasoning.

## Requirements

### Requirement: Prompt evaluation endpoint
The service MUST accept `POST /apis/endpoints/prompts/evaluations` with a JSON body containing a non-empty string `prompt`, a non-empty string `answer`, and a non-empty `metrics` array. Each metric MUST include a `name` and a `threshold` from 0 to 1 inclusive. `name` MUST be `answer_relevancy`, `conciseness`, or `specificity`. Names in one request MUST be unique. The body MUST NOT contain a field the contract does not define.

#### Scenario: Valid prompt evaluation is accepted
- **WHEN** a client posts `prompt` `capital of France`, `answer` `Paris is the capital of France`, and metrics `answer_relevancy` at threshold `0.5` and `specificity` at threshold `0.5`
- **THEN** the response status is 200 and the body is a list with one entry per metric in that order

### Requirement: Prompt metric verdict
The response body MUST be a JSON list. Each item MUST contain `name`, `result`, and `reasoning`. `result` MUST be `pass` when that metric's score is greater than or equal to its own `threshold`, and `fail` otherwise. `reasoning` MUST explain the score.

#### Scenario: A lower threshold passes and a higher threshold fails
- **WHEN** conciseness for prompt `hello` and answer `hello there friend extra` is requested once at threshold `0.2` and once at threshold `0.9`
- **THEN** the first result is `pass` and the second result is `fail`

#### Scenario: Score equal to the threshold passes
- **WHEN** conciseness for prompt `hello` and answer `hello there` is requested at threshold `0.5`
- **THEN** that metric's `result` is `pass`

### Requirement: Prompt request validation
The service MUST reject an invalid prompt evaluation request with HTTP 422. The body MUST be a JSON list. Each item MUST contain `error_code` `VALIDATION_ERROR`, a `reason_code`, and a `message`. A missing field uses `reason_code` `MISSING_FIELD`. An unknown field uses `UNKNOWN_FIELD`. An empty `prompt` or empty `metrics` array uses `EMPTY`. A metric name outside the supported set uses `UNSUPPORTED_METRIC`. A repeated metric name uses `DUPLICATE_METRIC`. A `threshold` outside 0 to 1 uses `OUT_OF_RANGE`.

#### Scenario: Missing fields are listed
- **WHEN** a client posts an empty JSON object
- **THEN** the response status is 422 and the body lists `prompt`, `answer`, and `metrics` as `MISSING_FIELD`

#### Scenario: Unknown metric is rejected
- **WHEN** a client posts a metric named `bleu`
- **THEN** the response status is 422 and the body contains `reason_code` `UNSUPPORTED_METRIC`

### Requirement: Prompt metric classes
`answer_relevancy`, `conciseness`, and `specificity` MUST be `RootMetric` subclasses. `PromptEvaluation` MUST accept that list of metrics and score the same prompt and answer with each metric's threshold. A threshold outside 0 to 1 MUST be rejected by the metric.

#### Scenario: Metric construction rejects a threshold above 1
- **WHEN** an answer-relevancy metric is constructed with threshold `1.5`
- **THEN** construction raises an error stating the threshold must be between 0 and 1
