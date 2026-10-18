# FreeEval

FreeEval scores prompt, RAG, and agent results that the caller already produced. It does not call a model, retriever, or agent.

Runs are not stored. Contexts, relevant ids, and steps are accepted but not scored.

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

A case is scored with case-sensitive exact match only when an expected value is present. Comparison does not trim whitespace.

### Prompts

`POST /apis/endpoints/prompts/`

The route on the prompts router is `/`. The prefix is mounted by the API app. Each entry in `metrics` produces one verdict. `provider` is `deepeval` or `ragas`; those runners are reserved and currently return `status` `pending`.

```bash
curl -X POST http://127.0.0.1:8000/apis/endpoints/prompts/ \
  -H 'content-type: application/json' \
  -d '{"prompt":"What is 2+2?","response":"4","metrics":[{"name":"answer_relevancy","provider":"deepeval"}],"temperature":0,"threshold":0.7}'
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
