import uuid
from unittest.mock import patch

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_upload_document(client: AsyncClient) -> None:
    file_content = f"Test document content {uuid.uuid4()}".encode()
    files = {"file": ("test_doc.txt", file_content, "text/plain")}

    response = await client.post("/api/v1/documents/", files=files)

    assert response.status_code == 201
    data = response.json()
    assert "id" in data
    assert data["filename"] == "test_doc.txt"
    assert data["status"] == "pending"


@pytest.mark.asyncio
@patch("src.api.endpoints.documents.parse_document_task.delay")
async def test_upload_document_triggers_task(mock_delay, client: AsyncClient) -> None:
    file_content = f"Mock PDF or TXT content {uuid.uuid4()}".encode()
    files = {"file": ("test_pipeline.txt", file_content, "text/plain")}

    response = await client.post("/api/v1/documents/", files=files)

    assert response.status_code == 201
    mock_delay.assert_called_once()


@pytest.mark.asyncio
async def test_list_documents(client: AsyncClient) -> None:
    response = await client.get("/api/v1/documents/")

    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)

    if len(data) > 0:
        assert "id" in data[0]
        assert "filename" in data[0]
        assert "status" in data[0]
