import asyncio
import logging
import uuid

from langfuse.decorators import observe
from sqlalchemy import select

from src.core.config import settings
from src.core.database import AsyncSessionLocal
from src.core.elastic import es_client
from src.core.metrics import RAG_RETRIEVAL_LATENCY
from src.core.qdrant import qdrant_client
from src.models.chunk import DocumentChunk
from src.schemas.retrieval import RetrievedChunk
from src.services.embedding_service import generate_embeddings
from src.services.reranking_service import rerank_chunks

logger = logging.getLogger(__name__)


async def _search_qdrant(query_vector: list[float], top_k: int) -> list[str]:
    results = await qdrant_client.search(
        collection_name=settings.qdrant_collection_name,
        query_vector=query_vector,
        limit=top_k,
        with_payload=False,
    )
    return [str(point.id) for point in results]


async def _search_elasticsearch(query: str, top_k: int) -> list[str]:
    response = await es_client.search(
        index=settings.elastic_index_name,
        body={
            "query": {"match": {"text_content": query}},
            "size": top_k,
            "_source": False,
        },
    )
    hits = response["hits"]["hits"]
    return [hit["_id"] for hit in hits]


def _compute_rrf(qdrant_ids: list[str], es_ids: list[str], k: int = 60) -> list[str]:
    rrf_scores: dict[str, float] = {}
    for rank, chunk_id in enumerate(qdrant_ids):
        rrf_scores[chunk_id] = rrf_scores.get(chunk_id, 0.0) + (1.0 / (k + rank + 1))
    for rank, chunk_id in enumerate(es_ids):
        rrf_scores[chunk_id] = rrf_scores.get(chunk_id, 0.0) + (1.0 / (k + rank + 1))
    sorted_items = sorted(rrf_scores.items(), key=lambda x: x[1], reverse=True)
    return [item[0] for item in sorted_items]


@RAG_RETRIEVAL_LATENCY.time()
@observe(name="hybrid_retrieval_and_rerank")
async def retrieve_and_rerank(
    query: str,
    top_k_retrieve: int = 20,
    top_k_return: int = 5,
    score_threshold: float = 0.0,
) -> list[RetrievedChunk]:
    query_vector = generate_embeddings([query])[0]
    qdrant_task = _search_qdrant(query_vector, top_k_retrieve)
    es_task = _search_elasticsearch(query, top_k_retrieve)
    qdrant_ids, es_ids = await asyncio.gather(qdrant_task, es_task)

    if not qdrant_ids and not es_ids:
        return []

    fused_ids = _compute_rrf(qdrant_ids, es_ids)
    target_ids = fused_ids[:top_k_retrieve]
    chunk_uuids = [uuid.UUID(cid) for cid in target_ids]

    async with AsyncSessionLocal() as db:
        stmt = select(DocumentChunk).where(DocumentChunk.id.in_(chunk_uuids))
        result = await db.execute(stmt)
        db_chunks = {str(c.id): c for c in result.scalars().all()}

    chunks_to_rerank = []
    for chunk_id in target_ids:
        db_chunk = db_chunks.get(chunk_id)
        if db_chunk:
            chunks_to_rerank.append(
                {
                    "chunk_id": chunk_id,
                    "document_id": str(db_chunk.document_id),
                    "text_content": db_chunk.text_content,
                    "metadata_json": db_chunk.metadata_json,
                    "retrieval_score": 0.0,
                }
            )

    reranked_chunks = await asyncio.to_thread(rerank_chunks, query, chunks_to_rerank)

    filtered_chunks = [
        chunk for chunk in reranked_chunks if chunk["rerank_score"] >= score_threshold
    ]
    final_results = filtered_chunks[:top_k_return]

    return [RetrievedChunk(**chunk) for chunk in final_results]
