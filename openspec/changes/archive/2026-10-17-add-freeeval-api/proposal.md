# Proposal

## Why

FreeEval has no package, process entry, or HTTP surface, so prompt, RAG, and agent evaluations cannot be submitted or compared through one contract. This change stands up that API first, before model providers, retrieval metrics, or agent sandboxes exist.

## What Changes

- Add the `freeeval` Python package under `src/freeeval`, with `main.py` as the process entry, a settings module loaded from the environment, a root `README.md`, and a root `.env.example`.
- Add an HTTP API layer at `src/freeeval/api`, with use-case routers under `src/freeeval/api/apis`, mounted at `/apis`.
- Add three evaluation endpoints that accept already-produced results and return a scored run record:
  - `POST /apis/endpoints/prompts/evaluations` for prompt cases
  - `POST /apis/endpoints/rag/evaluations` for RAG cases
  - `POST /apis/endpoints/agents/evaluations` for agent cases
- Code evaluation and summarization evaluation are deferred until their request fields are specified.
- Score a case with exact match when the caller supplies an expected value. Accept an unscored case when the expected value is omitted. Reject an invalid body with a validation error.
- Add `GET /health` so the process can be checked without running an evaluation.
- The service does not call models, retrievers, tools, or other systems under test. Callers send the output, the contexts, or the trajectory they already have.

API layer must be standardised using FAST API, must be extensible, decoupled

## Capabilities

### New Capabilities

- `service-bootstrap`: The process starts from documented environment settings and exposes a health check.
- `prompt-evaluation`: Callers submit prompt cases and receive exact-match scores when an expected output is present.
- `rag-evaluation`: Callers submit RAG cases, including retrieved contexts, and receive exact-match scores when an expected answer is present.
- `agent-evaluation`: Callers submit agent cases, including the step trajectory, and receive exact-match scores when an expected output is present.

### Modified Capabilities

- None. The repository has no existing specs.

## Impact

- New source tree: `src/freeeval/main.py`, `src/freeeval/config.py`, `src/freeeval/api/`, and `src/freeeval/api/apis/`.
- New project files: `README.md`, `.env.example`, and `pyproject.toml` (package metadata and dependencies required by the `src` layout).
- New HTTP surface: `GET /health`, `POST /apis/endpoints/prompts/evaluations`, `POST /apis/endpoints/rag/evaluations`, `POST /apis/endpoints/agents/evaluations`.
- New runtime dependencies: FastAPI, Uvicorn, and Pydantic Settings. Test dependencies: pytest and HTTPX.
- No existing code, APIs, or published specs change. No secrets are committed; `.env.example` holds names and defaults only.
