from fastapi import FastAPI

from freeeval.api.apis import routers
from freeeval.api.apis.endpoints.prompts import router as prompts_router
from freeeval.api.apis.main import PROMPTS_PREFIX


def create_app() -> FastAPI:
    app = FastAPI(title="FreeEval")

    @app.get("/health")
    def health() -> dict[str, str]:
        return {"status": "ok"}

    for router in routers:
        if router is prompts_router:
            app.include_router(router, prefix=PROMPTS_PREFIX)
        else:
            app.include_router(router)
    return app
