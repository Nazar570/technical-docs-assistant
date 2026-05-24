from fastapi import APIRouter

from src.schemas.retrieval import SearchRequest, SearchResponse
from src.services import retrieval_service

router = APIRouter()


@router.post("/search", response_model=SearchResponse)
async def search_documents(request: SearchRequest) -> SearchResponse:
    results = await retrieval_service.retrieve_and_rerank(
        query=request.query,
        top_k_retrieve=request.top_k_retrieve,
        top_k_return=request.top_k_return,
    )

    return SearchResponse(query=request.query, results=results)
