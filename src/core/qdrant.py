import logging

from qdrant_client import AsyncQdrantClient
from qdrant_client.http import models

from src.core.config import settings

logger = logging.getLogger(__name__)

qdrant_client = AsyncQdrantClient(host=settings.qdrant_host, port=settings.qdrant_port)


async def init_qdrant() -> None:
    collections = await qdrant_client.get_collections()
    collection_names = [c.name for c in collections.collections]

    if settings.qdrant_collection_name not in collection_names:
        logger.info(f"Creating Qdrant collection: {settings.qdrant_collection_name}")
        await qdrant_client.create_collection(
            collection_name=settings.qdrant_collection_name,
            vectors_config=models.VectorParams(
                size=settings.embedding_dim,
                distance=models.Distance.COSINE,
            ),
        )
    else:
        logger.info(
            f"Qdrant collection '{settings.qdrant_collection_name}' already exists."
        )
