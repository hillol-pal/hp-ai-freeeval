# Design

## Context

The repository has an OpenSpec root and no Python package. The behavioral contract is in the delta specs under this change. See `proposal.md` for why the API comes before providers and metrics.

The service is local and greenfield. Default bind address stays on loopback. Run records are not stored.

## Goals / Non-Goals

**Goals:**

- One installable `freeeval` package whose HTTP layer lives at `src/freeeval/api` and whose use-case routers live at `src/freeeval/api/apis`.
- Request models that reject unknown fields, and one shared run-record response for the three evaluation routes.
- One exact-match function used by every use case, so the three routes cannot drift on comparison or summary counts.
- Settings loaded from the environment, with operator docs that name the same variables.

**Non-Goals:**

- Calling a model, retriever, or agent.
- Code evaluation and summarization evaluation routes.
- Scores other than `exact_match`.
- Persisting runs, authentication, or a user interface.
- A second scorer interface. Add that when a second score exists.

## Decisions

### FastAPI and Pydantic v2

FastAPI maps schema violations to HTTP 422, which is the status the evaluation specs require. Pydantic models with `extra="forbid"` reject fields the contract does not define. Pydantic Settings loads `FREEEVAL_*` variables and fails construction when `port` is outside 1–65535.

Alternatives considered: Flask leaves validation and error status to hand-written code. A raw ASGI app does the same. Neither buys the 422 behavior.

### Package layout

```text
pyproject.toml
README.md
.env.example
.gitignore
src/freeeval/
  __init__.py
  __main__.py          # calls main()
  main.py              # builds the app and runs uvicorn
  config.py            # Settings
  api/
    __init__.py
    app.py             # create_app(): health + router includes
    schemas.py         # request models, Score, CaseResult, Summary, RunRecord
    scoring.py         # exact_match and summary
    apis/
      __init__.py
      prompts.py       # POST /evaluations, mounted at /apis/endpoints/prompts
      rag.py           # mounted at /apis/endpoints/rag
      agents.py        # mounted at /apis/endpoints/agents
tests/
  test_config.py
  test_health.py
  test_prompt_evaluation.py
  test_rag_evaluation.py
  test_agent_evaluation.py
```

`pyproject.toml` uses the hatchling build backend and maps the `src` directory onto the `freeeval` package. Python requirement is 3.11 or newer. Runtime dependencies are FastAPI, Uvicorn, and Pydantic Settings. Dev dependencies are pytest and HTTPX.

`python -m freeeval` is the documented start command. `main()` loads settings, configures logging from `log_level`, and calls `uvicorn.run` with `settings.host` and `settings.port`. A missing `.env` file is not an error. An invalid port raises during settings construction, `main()` does not catch it, and the process exits without calling `uvicorn.run`.

### Settings fields

| Environment variable | Settings field | Default |
| --- | --- | --- |
| `FREEEVAL_HOST` | `host` | `127.0.0.1` |
| `FREEEVAL_PORT` | `port` | `8000` |
| `FREEEVAL_LOG_LEVEL` | `log_level` | `info` |
| `FREEEVAL_ENV` | `environment` | `local` |

Prefix is `FREEEVAL_`. The field is `environment` so it does not shadow Python's `env`. Startup logs the environment name, which is how the process uses `FREEEVAL_ENV`. `.env.example` lists the four names and defaults and nothing else. `.gitignore` ignores `.env`.

### Routes and models

`create_app()` registers `GET /health` and includes the routers exported by `api/apis/__init__.py`. Each use case is its own module, so a later route is a new module plus one list entry. The prefix is `/apis/endpoints/<use-case>` so prompt, RAG, and agent routes sit beside future use cases.

| Router | Prefix | Route |
| --- | --- | --- |
| `apis/prompts.py` | `/apis/endpoints/prompts` | `POST /evaluations` |
| `apis/rag.py` | `/apis/endpoints/rag` | `POST /evaluations` |
| `apis/agents.py` | `/apis/endpoints/agents` | `POST /evaluations` |

Code evaluation and summarization evaluation are not in this change. Their request fields are not specified yet.

Shared response models in `schemas.py`:

- `Score`: `name` is `exact_match`, `value` and `passed` are booleans.
- `CaseResult`: `case_id`, `scores`.
- `Summary`: `case_count`, `scored_count`, `passed_count`.
- `RunRecord`: `run_id`, `use_case` (`prompt`, `rag`, or `agent`), `results`, `summary`.

Request models, also `extra="forbid"`:

- Prompt case: `id`, `input` object, `output` string, optional `expected` string.
- RAG case: `id`, `question`, `answer`, `contexts` (each `id` and `text`), optional `expected_answer`, optional `relevant_context_ids`.
- Agent case: `id`, `task`, `output`, `steps`, optional `expected_output`.
- Agent step: `kind` in `model`, `retrieve`, `tool`, `observe`; non-empty `name`; optional `input` object, `output` object, and `error` string.

A request validator rejects duplicate case ids. `id` and step `name` and context `id` use a non-empty constraint. `run_id` is a new UUID4 hex string per request and is not stored.

### Scoring

`scoring.exact_scores(actual, expected)` returns `[]` when `expected` is omitted. Otherwise it returns one `exact_match` score whose `value` and `passed` are `actual == expected`, with no trimming or case folding.

`scoring.summarize(results)` sets `case_count` to the result length, `scored_count` to how many results have a score, and `passed_count` to how many of those scores have `passed` true. Each router calls these two functions and does not reimplement them. RAG passes `answer` and `expected_answer`. Agents pass `output` and `expected_output`. Contexts, relevant ids, and steps are validated and then ignored by the scorer.

### Tests

HTTP tests use FastAPI's `TestClient` (HTTPX) and do not bind a port. Config tests construct `Settings` for defaults, overrides, and an invalid port. One test monkeypatches `uvicorn.run` and asserts `main()` passes the configured host and port, and that an invalid port never reaches `uvicorn.run`.

### Operator docs

`README.md` states that this service scores outputs the caller already has, shows the four variables, the start command, `GET /health`, and one request example for each evaluation route. It states that runs are not stored and that retrieval and trajectory fields are accepted but not scored.

## Risks / Trade-offs

- [Exact match is a thin stand-in for evaluation] → The README and this design state the limit. The score name is `exact_match`, so a later metric does not reuse a generic `score` field.
- [Three routers copy the run-record assembly] → Response models and `scoring.py` are shared. Routers only map their case fields.
- [`extra="forbid"` rejects helpful extras such as `metadata`] → The specs require rejection. A later change can add an explicit metadata object.
- [Run ids cannot be fetched later] → Documented. Persistence is its own change.
- [Default exposure] → Host defaults to `127.0.0.1`. Binding a wider address requires `FREEEVAL_HOST`.
- [`.env` secrets] → `.env.example` has defaults only, and `.gitignore` excludes `.env`.

## Migration Plan

There is no deployed service and no existing package. Installing the new package is the whole rollout. Rollback is removing the package and the process that runs it. No data migration.

## Open Questions

None. Endpoint paths, score behavior, and the decision to score caller-supplied outputs are fixed by the specs.
