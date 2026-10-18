from fastapi import FastAPI

from freeeval.api.apis.endpoints import agents, prompts, rag

PROMPTS_PREFIX = "/apis/endpoints/prompts"

app = FastAPI(
    title="FreeEval",
    description="FreeEval HTTP API for prompt, RAG, and agent evaluation.",
    version="0.1.0",)


@app.get("/")
async def root():
    """ Root endpoint for the FreeEval API."""

    return {"message": "Welcome to the FreeEval API!",
            "description": "This API provides endpoints for evaluating prompts"
            ", RAG (Retrieval-Augmented Generation), and agents."}


app.include_router(
    prefix="/apis/endpoints/rag",
    tags=["apis"],
    router=rag.router,
)

app.include_router(
    prompts.router,
    prefix=PROMPTS_PREFIX,
)

app.include_router(
    prefix="/apis/endpoints/agents",
    tags=["apis"],
    router=agents.router,
)

