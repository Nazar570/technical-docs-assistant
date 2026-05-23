from fastapi import FastAPI

from src.core.config import settings

app = FastAPI(
    title=settings.project_name,
    version=settings.version,
    openapi_url=f"{settings.api_v1_str}/openapi.json",
)


@app.get("/health", tags=["System"])
async def health_check() -> dict[str, str]:
    """
    Check if the API is running and responsive.
    """
    return {
        "status": "ok",
        "environment": settings.environment,
        "version": settings.version,
    }
