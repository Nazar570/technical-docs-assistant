from fastapi import APIRouter

from src.api.endpoints import documents, qa, retrieval

api_router = APIRouter()
api_router.include_router(documents.router, prefix="/documents", tags=["Documents"])
api_router.include_router(retrieval.router, prefix="/retrieval", tags=["Retrieval"])
api_router.include_router(qa.router, prefix="/qa", tags=["Q&A"])
