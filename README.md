# FreeEval

FreeEval scores prompt, code, RAG, and agent results that the caller already produced. RAG metrics call the configured judge model. Prompt metrics score the prompt and answer directly. Code and agent routes do not call a model.

Runs are not stored. Contexts, relevant ids, and steps are accepted but not scored. Code snippets are accepted but not scored.

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

Code, RAG, and agent cases are scored with case-sensitive exact match only when an expected value is present. Comparison does not trim whitespace. Prompt evaluation uses the metrics and threshold in the request.

### Prompts

`POST /apis/endpoints/prompts/evaluations`

The body is the input `prompt`, the model `answer`, and a `metrics` list. Each metric has a `name` and its own `threshold` from 0 to 1. A metric passes when its score is greater than or equal to that threshold. The response is a JSON list with one object per metric, in request order: `name`, `result` (`pass` or `fail`), and `reasoning`.

Metric names are listed under [Metrics](#metrics).

A failed request returns a JSON list. Each item has `error_code`, `reason_code`, and `message`. Validation problems use HTTP 422.

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

```bash
curl -X POST http://127.0.0.1:8000/apis/endpoints/rag/evaluations \
  -H 'content-type: application/json' \
  -d '{"cases":[{"id":"r1","question":"Capital of France?","answer":"Paris","contexts":[{"id":"c1","text":"Paris is the capital."}],"expected_answer":"Paris"}]}'
```

### Agents

`POST /apis/endpoints/agents/evaluations`

```bash
curl -X POST http://127.0.0.1:8000/apis/endpoints/agents/evaluations \
  -H 'content-type: application/json' \
  -d '{"cases":[{"id":"a1","task":"Find the capital","output":"Paris","steps":[{"kind":"tool","name":"search"}],"expected_output":"Paris"}]}'
```

## Metrics

Add a metric to the list for its category when that metric becomes supported.

### Prompt

- `answer_relevancy` — share of prompt content words that also appear in the answer.
- `conciseness` — 1 when the answer is no longer than the prompt, otherwise the length ratio.
- `specificity` — share of answer words that are content words rather than stopwords.

### Code

- `exact_match` — scored on `POST /apis/endpoints/code/evaluations` when `expected` is present.
- `code_readability` — class in `src/freeeval/metrics/code/code_readability.py`. The code evaluation route does not select it yet.

### RAG

- `exact_match` — scored when `expected_answer` is present.
- `faithfulness` — DeepEval score of the answer against the retrieved contexts.
- `answer_relevancy` — DeepEval score of the answer against the question.

### Agents

- `exact_match` — scored on `POST /apis/endpoints/agents/evaluations` when `expected_output` is present.

### Agentic

None yet.

### Ethical

None yet.

### Summarisation

None yet.

