# Tasks

## 1. Package and settings

- [x] 1.1 Add `pyproject.toml` for the `freeeval` package (Python 3.11+, hatchling, `src` layout, FastAPI, Uvicorn, Pydantic Settings, and dev extras pytest and HTTPX) and verify `uv sync --extra dev` or `pip install -e ".[dev]"` succeeds.
- [x] 1.2 Add `src/freeeval/__init__.py`, `src/freeeval/api/__init__.py`, `src/freeeval/api/apis/__init__.py`, and a `.gitignore` that ignores `.env`, and verify `python -c "import freeeval"` succeeds after install.
- [x] 1.3 Add `src/freeeval/config.py` with `FREEEVAL_HOST`, `FREEEVAL_PORT`, `FREEEVAL_LOG_LEVEL`, and `FREEEVAL_ENV` mapped to `host`, `port`, `log_level`, and `environment`, defaults `127.0.0.1`, `8000`, `info`, and `local`, and port constrained to 1–65535. Verify `tests/test_config.py` covers defaults, an override of each variable, and rejection of port `abc` and port `0`.
- [x] 1.4 Add `.env.example` listing only those four variables and the same defaults, with no secrets. Verify a test reads the file and asserts those names and defaults.

## 2. Process entry and health

- [x] 2.1 Add `create_app()` in `src/freeeval/api/app.py` with `GET /health` returning HTTP 200 and `{"status": "ok"}`. Verify `tests/test_health.py` covers a bodyless GET.
- [x] 2.2 Add `src/freeeval/main.py` and `src/freeeval/__main__.py` so `python -m freeeval` loads settings, logs the environment name, and calls `uvicorn.run` with that host and port. Do not catch settings validation errors. Verify a test monkeypatches `uvicorn.run` and shows the configured host and port are passed, and that port `abc` exits without calling `uvicorn.run`.
- [x] 2.3 Document install, the four variables, `python -m freeeval`, and `GET /health` in `README.md`. Verify the README contains those variable names, that start command, and the health path.

## 3. Shared evaluation contract

- [x] 3.1 Add request and response models in `src/freeeval/api/schemas.py` with `extra="forbid"`: shared `Score`, `CaseResult`, `Summary`, and `RunRecord`; prompt, RAG, and agent case models from the delta specs, including non-empty ids, agent step `kind` limited to `model`, `retrieve`, `tool`, and `observe`, and duplicate case-id rejection. Verify model tests accept one valid payload per use case and reject an unknown field, an empty id, a duplicate id, and agent step kind `browse`.
- [x] 3.2 Add `exact_scores` and `summarize` in `src/freeeval/api/scoring.py`. Exact match is case-sensitive and does not trim. Omitted expected values produce no score. Verify unit tests for equal strings, unequal strings, a whitespace difference, an omitted expected value, and a summary of two results where only one is scored and passed.

## 4. Prompt evaluation API

- [x] 4.1 Add `POST /apis/endpoints/prompts/evaluations` in `src/freeeval/api/apis/prompts.py`, using `exact_scores` on `output` and `expected` and `summarize` for the run record. Return a new UUID hex `run_id` and `use_case` `prompt`. Verify `tests/test_prompt_evaluation.py` covers a valid case, missing `output` (422 and no `run_id`), an unknown field (422), identical and different outputs, an omitted `expected`, a two-case summary of `case_count` 2, `scored_count` 1, `passed_count` 1, and two requests receiving different `run_id` values.
- [x] 4.2 Add a prompt request example to `README.md`. Verify the example posts to `POST /apis/endpoints/prompts/evaluations` and includes `id`, `input`, `output`, and `expected`.

## 5. RAG evaluation API

- [x] 5.1 Add `POST /apis/endpoints/rag/evaluations` in `src/freeeval/api/apis/rag.py`, using `exact_scores` on `answer` and `expected_answer`. Validate contexts and `relevant_context_ids`, and do not use them in the score. Verify `tests/test_rag_evaluation.py` covers a valid case, a context missing `text` (422 and no `run_id`), identical answers, matching answers with non-matching `relevant_context_ids` still passing, an omitted `expected_answer`, and a two-case summary of 2, 1, and 1.
- [x] 5.2 Add a RAG request example to `README.md`. Verify the example posts to `POST /apis/endpoints/rag/evaluations` and includes `question`, `answer`, `contexts`, and `expected_answer`.

## 6. Agent evaluation API

- [x] 6.1 Add `POST /apis/endpoints/agents/evaluations` in `src/freeeval/api/apis/agents.py`, using `exact_scores` on `output` and `expected_output`. Validate `steps` and do not use them in the score. Verify `tests/test_agent_evaluation.py` covers a valid case with a `tool` step, an empty `steps` array, a step that also includes `input`, `output`, and `error`, step kind `browse` (422 and no `run_id`), identical outputs, a passing score when a step has a non-empty `error`, an omitted `expected_output`, and a two-case summary of 2, 1, and 1.
- [x] 6.2 Add an agent request example to `README.md`, and state that runs are not stored and that contexts, relevant ids, and steps are accepted but not scored. Verify the README shows `POST /apis/endpoints/agents/evaluations` with `task`, `output`, `steps`, and `expected_output`, and includes those two limits.

## 7. Integration

- [x] 7.1 Run the full test suite from a clean install and verify every test in `tests/` passes.

## Workflow follow-up

- Archive the change after implementation and review.
- Verify the archived specs under `openspec/specs/`.
