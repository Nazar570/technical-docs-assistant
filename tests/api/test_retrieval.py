from unittest.mock import AsyncMock, patch

import pytest
from httpx import AsyncClient

from src.schemas.retrieval import RetrievedChunk


@pytest.mark.asyncio
@patch(
    "src.api.endpoints.retrieval.retrieval_service.retrieve_and_rerank",
    new_callable=AsyncMock,
)
async def test_search_endpoint(mock_retrieve, client: AsyncClient) -> None:
    mock_retrieve.return_value = [
        RetrievedChunk(
            chunk_id="123e4567-e89b-12d3-a456-426614174000",
            document_id="123e4567-e89b-12d3-a456-426614174001",
            text_content="Mocked machine learning content.",
            metadata_json={},
            retrieval_score=0.9,
            rerank_score=0.95,
        )
    ]

    payload = {
        "query": "machine learning architecture",
        "top_k_retrieve": 5,
        "top_k_return": 2,
    }

    response = await client.post("/api/v1/retrieval/search", json=payload)

    assert response.status_code == 200
    data = response.json()
    assert data["query"] == payload["query"]
    assert len(data["results"]) == 1
    assert data["results"][0]["text_content"] == "Mocked machine learning content."
