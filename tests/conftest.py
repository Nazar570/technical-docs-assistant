from collections.abc import AsyncGenerator

import pytest
from httpx import AsyncClient

from src.api.main import app


@pytest.fixture
async def client() -> AsyncGenerator[AsyncClient, None]:
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac
