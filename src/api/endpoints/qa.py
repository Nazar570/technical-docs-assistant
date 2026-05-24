from fastapi import APIRouter
from langfuse.decorators import observe

from src.schemas.qa import AskRequest, AskResponse
from src.services import generation_service, retrieval_service

router = APIRouter()


@router.post("/ask", response_model=AskResponse)
@observe(name="ask_endpoint", capture_input=False, capture_output=False)
async def ask_question(request: AskRequest) -> AskResponse:
    retrieved_chunks = await retrieval_service.retrieve_and_rerank(
        query=request.query,
        top_k_retrieve=request.top_k_retrieve,
        top_k_return=request.top_k_return,
        score_threshold=request.score_threshold,
    )

    if not retrieved_chunks:
        return AskResponse(
            query=request.query,
            answer=(
                "I could not find any highly relevant information in the "
                "uploaded documents to answer your question."
            ),
            citations=[],
        )

    answer = generation_service.generate_grounded_answer(
        query=request.query, chunks=retrieved_chunks
    )

    return AskResponse(query=request.query, answer=answer, citations=retrieved_chunks)
