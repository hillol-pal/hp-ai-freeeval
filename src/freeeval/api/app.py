from fastapi import FastAPI

from freeeval.api.routers import agents, code, prompts, rag

API_PREFIX = "/apis/endpoints"


def create_app() -> FastAPI:
    app = FastAPI(
        title="FreeEval",
        description="FreeEval HTTP API for prompt, code, RAG, and agent evaluation.",
        version="0.1.0",
        docs_url="/swagger",      # change Swagger URL
        redoc_url="/documentation",
        openapi_url="/openapi.json",  # raw OpenAPI schema
    )

    @app.get("/health")
    def health() -> dict[str, str]:
        return {"status": "ok"}

    app.include_router(prompts.router, prefix=API_PREFIX)
    app.include_router(code.router, prefix=API_PREFIX)
    app.include_router(rag.router, prefix=API_PREFIX)
    app.include_router(agents.router, prefix=API_PREFIX)
    return app
