from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.exception_handlers import request_validation_exception_handler
from fastapi.responses import JSONResponse

from freeeval.api.errors import validation_errors
from freeeval.api.routers import agents, code, prompts, rag
from freeeval.tracing import configure_phoenix

API_PREFIX = "/apis/endpoints"
LIST_ERROR_PATHS = {
    f"{API_PREFIX}/prompts/evaluations",
    f"{API_PREFIX}/rag/evaluations",
    f"{API_PREFIX}/agents/evaluations",
}


def create_app() -> FastAPI:
    configure_phoenix()
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

    @app.exception_handler(RequestValidationError)
    async def list_validation_handler(
        request: Request, exc: RequestValidationError
    ) -> JSONResponse:
        if request.url.path.rstrip("/") not in LIST_ERROR_PATHS:
            return await request_validation_exception_handler(request, exc)
        body = [item.model_dump() for item in validation_errors(exc)]
        return JSONResponse(status_code=422, content=body)

    app.include_router(prompts.router, prefix=API_PREFIX)
    app.include_router(code.router, prefix=API_PREFIX)
    app.include_router(rag.router, prefix=API_PREFIX)
    app.include_router(agents.router, prefix=API_PREFIX)
    return app
