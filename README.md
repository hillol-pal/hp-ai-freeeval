# FreeEval

FreeEval scores prompt, code, RAG, and agent results that the caller already produced. Prompt, RAG, and agent routes score the request with the metrics the caller lists. The code route scores an exact match when an expected value is present.

The default `framework` is `freeeval`, which does not call a model. `deepeval` and `ragas` call the configured OpenAI judge for metrics they support. Any other metric in that request is scored by FreeEval. Each result includes `implementation` (`freeeval`, `deepeval`, or `ragas`).

Runs are not stored. RAG `metadata` and agent `metadata` are accepted and are not scored. Code snippets are accepted and are not scored.

## Install

Requires Python 3.11 or newer.

```bash
uv sync --extra dev
```

## Configuration

The process reads these variables. When they are unset, it uses the defaults in `.env.example`.

| Variable | Default |
| --- | --- |
| `FREEEVAL_HOST` | `127.0.0.1` |
| `FREEEVAL_PORT` | `8000` |
| `FREEEVAL_LOG_LEVEL` | `info` |
| `FREEEVAL_ENV` | `local` |

Copy `.env.example` to `.env` to override them. Do not commit `.env`.

## Tracing

Evaluation calls are OpenTelemetry spans. Set `PHOENIX_COLLECTOR_ENDPOINT` to an [Arize Phoenix](https://arize.com/docs/phoenix) collector and the process registers that collector at startup. `PHOENIX_PROJECT_NAME` defaults to `freeeval`. Set `PHOENIX_API_KEY` when the collector requires one. `FREEEVAL_PHOENIX_ENABLED=true` turns export on even when those variables are unset, which sends spans to `http://localhost:6006`. `FREEEVAL_PHOENIX_ENABLED=false` turns export off.

A local collector is a separate process: `uvx arize-phoenix serve`. This API does not start it.

Each request is one `CHAIN` span named `freeeval.prompt`, `freeeval.rag`, `freeeval.agent`, or `freeeval.code`. The span carries the same `run_id` as a successful response, the request JSON, and the result JSON. Each metric is an `EVALUATOR` child span. OpenAI judge calls nest under that metric span.

## Run

```bash
uv run python -m freeeval
```

`python -m freeeval` listens on `FREEEVAL_HOST` and `FREEEVAL_PORT`.

## Health

```bash
curl http://127.0.0.1:8000/health
```

`GET /health` returns `{"status": "ok"}`.

## Evaluations

Code cases are scored with case-sensitive exact match only when an expected value is present. Comparison does not trim whitespace. Prompt, RAG, and agent evaluation use the metrics and thresholds in the request.

### Prompts

`POST /apis/endpoints/prompts/evaluations`

The body is the input `prompt`, the model `answer`, a `metrics` list, and an optional `framework` (`freeeval`, `deepeval`, or `ragas`). Each metric has a `name` and its own `threshold` from 0 to 1. A metric passes when its score is greater than or equal to that threshold. The response is a JSON object with `run_id`, `framework`, and a `metrics` list. Each metric object has `name`, `result` (`pass` or `fail`), `reasoning`, and `implementation`, in request order.

The route currently accepts `answer_relevancy`, `conciseness`, and `specificity`. The full catalog is under [Metrics](#metrics).

A failed request returns a JSON list. Each item has `error_code`, `reason_code`, and `message`. Validation problems use HTTP 422. A missing judge configuration uses HTTP 503. A judge failure uses HTTP 502. Those responses have no `run_id`.

```bash
curl -X POST http://127.0.0.1:8000/apis/endpoints/prompts/evaluations \
  -H 'content-type: application/json' \
  -d '{"prompt":"What is 2+2?","answer":"4","metrics":[{"name":"answer_relevancy","threshold":0.7}]}'
```

### Code

`POST /apis/endpoints/code/evaluations`

```bash
curl -X POST http://127.0.0.1:8000/apis/endpoints/code/evaluations \
  -H 'content-type: application/json' \
  -d '{"cases":[{"id":"c1","code":"print(2 + 2)","output":"4","expected":"4"}]}'
```

### RAG

`POST /apis/endpoints/rag/evaluations`

The body is the `query`, the `actual_response`, the `retrieved_contexts` list, a `metrics` list, optional `metadata`, and an optional `framework`. Each metric has a `name` and its own `threshold` from 0 to 1. A metric passes when its score is greater than or equal to that threshold. The response has the same shape as prompt evaluation: `run_id`, `framework`, and a `metrics` list of `name`, `result` (`pass` or `fail`), `reasoning`, and `implementation`.

The route currently accepts `faithfulness` and `answer_relevancy`. Those scores use the query, the response, and the retrieved contexts. `metadata` is not scored. The full catalog is under [Metrics](#metrics).

A failed request returns a JSON list. Each item has `error_code`, `reason_code`, and `message`. Validation problems use HTTP 422. A missing judge configuration uses HTTP 503. A judge failure uses HTTP 502. Those responses have no `run_id`.

```bash
curl -X POST http://127.0.0.1:8000/apis/endpoints/rag/evaluations \
  -H 'content-type: application/json' \
  -d '{"query":"Capital of France?","actual_response":"Paris is the capital of France.","retrieved_contexts":["Paris is the capital of France."],"metrics":[{"name":"faithfulness","threshold":0.7}],"metadata":{"source":"docs"}}'
```

### Agents

`POST /apis/endpoints/agents/evaluations`

The body is the task `input`, the `actual_output`, the `execution_trace` list, a `metrics` list, optional `metadata`, and an optional `framework`. Each metric has a `name` and its own `threshold` from 0 to 1. A metric passes when its score is greater than or equal to that threshold. The response has the same shape as prompt and RAG evaluation: `run_id`, `framework`, and a `metrics` list of `name`, `result` (`pass` or `fail`), `reasoning`, and `implementation`.

The route currently accepts `task_success_rate` and `tool_call_accuracy`. One execution succeeds when its output is non-empty and no trace event has an error. Tool accuracy compares each `tool` event's name and `arguments` with that event's `expected_name` and `expected_arguments`. `metadata` is not scored. `task_reliability` stays in the catalog because this request is one execution, not repeated trials. The full catalog is under [Metrics](#metrics).

A failed request returns a JSON list. Each item has `error_code`, `reason_code`, and `message`. Validation problems use HTTP 422. A missing judge configuration uses HTTP 503. A judge failure uses HTTP 502. Those responses have no `run_id`.

```bash
curl -X POST http://127.0.0.1:8000/apis/endpoints/agents/evaluations \
  -H 'content-type: application/json' \
  -d '{"input":"Find the capital of France","actual_output":"Paris","execution_trace":[{"kind":"tool","name":"search","arguments":{"q":"capital of France"},"expected_name":"search","expected_arguments":{"q":"capital of France"}}],"metrics":[{"name":"task_success_rate","threshold":0.5}],"metadata":{"source":"docs"}}'
```

## Metrics

Add a row to this table when another metric becomes supported. A higher score is better. For hallucination rate, the score is the desirable form of that measurement and the metric's reasoning states the raw rate.

| Category | Priority | Evaluation Metric | What It Measures |
| --- | --- | --- | --- |
| Code Generation | 1 | `maintainability` | Nesting, length, and branches of each function |
| Code Generation | 2 | `readability` | Line length, indentation, and conventional names |
| Code Generation | 3 | `robustness` | Share of functions that raise or catch an exception |
| Code Generation | 4 | `secured_code` | Absence of eval, exec, shell execution, deserialization, and hardcoded secrets |
| Code Generation | 5 | `extensibility` | Named units, focused function size, and parameters |
| Prompt / LLM | 1 | `answer_correctness` | Factual accuracy of generated responses against ground truth |
| Prompt / LLM | 2 | `instruction_following_rate` | Whether responses comply with prompt instructions and constraints |
| Prompt / LLM | 3 | `answer_relevancy` | How well responses address the user's question |
| Prompt / LLM | 4 | `format_compliance_rate` | Whether output complies with required schemas or formats |
| Prompt / LLM | 5 | `hallucination_rate` | Frequency of fabricated or unsupported factual claims |
| RAG | 1 | `faithfulness` | Whether generated claims are supported by retrieved context |
| RAG | 2 | `context_precision` | Relevance and ranking quality of retrieved documents |
| RAG | 3 | `context_recall` | Whether retrieval captures the information needed for the answer |
| RAG | 4 | `answer_relevancy` | How closely the generated answer addresses the question |
| RAG | 5 | `answer_correctness` | Factual accuracy of the final answer against ground truth |
| AI Agents | 1 | `task_success_rate` | Percentage of agent tasks successfully completed |
| AI Agents | 2 | `tool_call_accuracy` | Correctness of tool selection and input arguments |
| AI Agents | 3 | `task_reliability` | Consistency of successful outcomes across repeated executions |

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md). The `data_generation` package builds fixed prompt, code, RAG, and agent requests for tests and manual checks.

