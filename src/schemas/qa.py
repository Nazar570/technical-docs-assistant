from pydantic import BaseModel, Field

from src.schemas.retrieval import RetrievedChunk


class AskRequest(BaseModel):
    query: str = Field(..., min_length=2)
    top_k_retrieve: int = Field(20)
    top_k_return: int = Field(5)
    score_threshold: float = Field(
        0.0, description="Minimum cross-encoder score to be considered relevant."
    )


class AskResponse(BaseModel):
    query: str
    answer: str
    citations: list[RetrievedChunk]
