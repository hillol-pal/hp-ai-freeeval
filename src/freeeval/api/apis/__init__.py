from freeeval.api.apis.endpoints.agents import router as agents_router
from freeeval.api.apis.endpoints.prompts import router as prompts_router
from freeeval.api.apis.endpoints.rag import router as rag_router

routers = [prompts_router, rag_router, agents_router]
