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

The route currently accepts `answer_relevancy`, `conciseness`, and `specificity`. The full catalog is under [Metrics](#metrics).

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

