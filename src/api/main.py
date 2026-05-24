from contextlib import asynccontextmanager

from fastapi import FastAPI
from prometheus_client import make_asgi_app

from src.api.router import api_router
from src.core.config import settings
from src.core.elastic import es_client, init_elasticsearch
from src.core.qdrant import init_qdrant


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_qdrant()
    await init_elasticsearch()
    yield
    await es_client.close()


app = FastAPI(
    title=settings.project_name,
    version=settings.version,
    openapi_url=f"{settings.api_v1_str}/openapi.json",
    lifespan=lifespan,
)

metrics_app = make_asgi_app()
app.mount("/metrics", metrics_app)

app.include_router(api_router, prefix=settings.api_v1_str)


@app.get("/health", tags=["System"])
async def health_check() -> dict[str, str]:
    return {
        "status": "ok",
        "environment": settings.environment,
        "version": settings.version,
    }
