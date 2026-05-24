from pydantic import BaseModel, Field


class SearchRequest(BaseModel):
    query: str = Field(..., min_length=2)
    top_k_retrieve: int = Field(20)
    top_k_return: int = Field(5)
    score_threshold: float = Field(
        0.0, description="Minimum cross-encoder score to be considered relevant."
    )


class RetrievedChunk(BaseModel):
    chunk_id: str
    document_id: str
    text_content: str
    metadata_json: dict
    retrieval_score: float
    rerank_score: float


class SearchResponse(BaseModel):
    query: str
    results: list[RetrievedChunk]
