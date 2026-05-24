import logging

from elasticsearch import AsyncElasticsearch

from src.core.config import settings

logger = logging.getLogger(__name__)

es_client = AsyncElasticsearch([settings.elastic_host])


async def init_elasticsearch() -> None:
    index_name = settings.elastic_index_name

    exists = await es_client.indices.exists(index=index_name)
    if not exists:
        logger.info(f"Creating Elasticsearch index: {index_name}")
        mapping = {
            "mappings": {
                "properties": {
                    "document_id": {"type": "keyword"},
                    "chunk_id": {"type": "keyword"},
                    "text_content": {"type": "text", "analyzer": "english"},
                    "chunk_index": {"type": "integer"},
                }
            }
        }
        await es_client.indices.create(index=index_name, body=mapping)
    else:
        logger.info(f"Elasticsearch index '{index_name}' already exists.")
