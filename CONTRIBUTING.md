# Contributing

FreeEval scores results the caller already produced. Prompt, RAG, and agent routes score the metrics named in the request. The optional `framework` is `freeeval`, `deepeval`, or `ragas`. Metrics the selected SDK does not support are scored by FreeEval. The code route scores exact match when an expected output is present. Only `deepeval` and `ragas` call a model, and they use `OPENAI_API_KEY` with `FREEEVAL_DEEPEVAL_MODEL`.

## Setup

Requires Python 3.11 or newer and [uv](https://docs.astral.sh/uv/).

```bash
uv sync --extra dev
```

Copy `.env.example` to `.env` to override `FREEEVAL_HOST`, `FREEEVAL_PORT`, `FREEEVAL_LOG_LEVEL`, or `FREEEVAL_ENV`. Do not commit `.env`.

## Run

```bash
uv run python -m freeeval
uv run pytest
```

The server listens on `FREEEVAL_HOST` and `FREEEVAL_PORT`. `GET /health` returns `{"status": "ok"}`.

## Layout

| Path | What it holds |
| --- | --- |
| `src/freeeval/api` | The FastAPI app, request and response models, and routers |
| `src/freeeval/metrics` | Metric classes, one class in its own module |
| `src/data_generation` | Fixed evaluation requests for tests and manual checks |
| `tests` | API and metric tests |
| `openspec/specs` | Current behavior for the HTTP routes |

Routers are included from `create_app()`. Public paths stay under `/apis/endpoints`.

## Evaluation changes

Prompt, RAG, and agent requests take the fields documented in the README, a `metrics` list, and, for RAG and agents, optional `metadata`. Each metric has its own threshold from 0 to 1. A metric passes when its score is greater than or equal to that threshold.

A successful prompt, RAG, or agent response is an object with `run_id` and `metrics`. Each metric item has `name`, `result` (`pass` or `fail`), and `reasoning`. An invalid request returns HTTP 422 and a list of `error_code`, `reason_code`, and `message`, with no `run_id`. The code route still returns a run record and uses FastAPI's default validation body.

Register a metric on a route only when that route's fields can supply the metric's inputs. Keep the other catalog classes importable, and say in the README which names the route accepts.

When a metric becomes supported, add its own module, cover it with a test, and add a row to the README metrics table. Update the matching file under `openspec/specs` when the HTTP contract changes.

## Test data

`data_generation` builds deterministic request bodies. It does not call a model.

```python
from data_generation import generate, generate_all

prompts = generate("prompt", count=2, seed=0)
everything = generate_all()
```

`generate` walks the catalog for `prompt`, `code`, `rag`, or `agent`. `count` must be at least 1 and `seed` must be at least 0. The walk starts at `seed` modulo the catalog length and repeats when `count` is longer than the catalog.

Each `Sample` has `category`, `name`, `body`, and `expected_results`. `body` is the JSON to post. `expected_results` maps a metric name to `pass` or `fail`. A code sample with an empty map has no `expected` output, so the route returns no scores. Code samples use `exact_match` for that route. They do not exercise the code-generation metric classes.

Add a new sample in the category module under `src/data_generation`. Keep names unique inside a category, and extend `tests/test_data_generation.py` so the sample validates and scores as labeled.

## Checks before a change

Run `uv run pytest`. Do not put secrets in samples, metadata, or commits.
