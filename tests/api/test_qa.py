from unittest.mock import AsyncMock, patch

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
@patch(
    "src.api.endpoints.qa.retrieval_service.retrieve_and_rerank", new_callable=AsyncMock
)
@patch("src.api.endpoints.qa.generation_service.generate_grounded_answer")
async def test_ask_endpoint_no_relevant_chunks(
    mock_generate,
    mock_retrieve,
    client: AsyncClient,
) -> None:
    mock_retrieve.return_value = []
    mock_generate.return_value = "This is a mocked answer."

    payload = {
        "query": "How does the caching system work?",
        "top_k_retrieve": 5,
        "top_k_return": 3,
    }

    response = await client.post("/api/v1/qa/ask", json=payload)

    assert response.status_code == 200
    data = response.json()
    assert data["query"] == payload["query"]
    assert data["answer"] == (
        "I could not find any highly relevant information in the uploaded documents "
        "to answer your question."
    )
    assert data["citations"] == []
    mock_generate.assert_not_called()
