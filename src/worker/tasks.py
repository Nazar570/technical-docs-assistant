import asyncio
import logging
import uuid
from pathlib import Path

from elasticsearch.helpers import async_bulk
from qdrant_client.http.models import PointStruct
from sqlalchemy import select

from src.core.config import settings
from src.core.database import AsyncSessionLocal
from src.core.elastic import es_client
from src.core.qdrant import qdrant_client
from src.models.chunk import DocumentChunk
from src.models.document import Document, DocumentStatus
from src.services.chunking_service import chunk_markdown_file
from src.services.embedding_service import generate_embeddings
from src.services.parsing_service import parse_document_to_markdown
from src.worker.celery_app import celery_app

logger = logging.getLogger(__name__)


async def process_document_async(document_id: uuid.UUID) -> None:
    async with AsyncSessionLocal() as db:
        stmt = select(Document).where(Document.id == document_id)
        result = await db.execute(stmt)
        doc = result.scalar_one_or_none()

        if not doc:
            logger.error(f"Document {document_id} not found.")
            return

        doc.status = DocumentStatus.PARSING
        await db.commit()

        try:
            source_path = Path(settings.storage_dir) / f"{doc.id}_{doc.filename}"
            markdown_content = parse_document_to_markdown(source_path)

            parsed_filename = f"{doc.id}_parsed.md"
            parsed_path = Path(settings.storage_dir) / parsed_filename
            parsed_path.write_text(markdown_content, encoding="utf-8")

            doc.status = DocumentStatus.CHUNKING
            await db.commit()

            chunk_data_list = chunk_markdown_file(parsed_path)

            db_chunks = [
                DocumentChunk(
                    document_id=doc.id,
                    chunk_index=data["chunk_index"],
                    text_content=data["text_content"],
                    metadata_json=data["metadata_json"],
                )
                for data in chunk_data_list
            ]
            db.add_all(db_chunks)
            await db.flush()

            doc.parsed_text_path = str(parsed_path)
            doc.status = DocumentStatus.INDEXING
            await db.commit()
            logger.info(f"Successfully chunked document {document_id}")

            texts_to_embed = [chunk.text_content for chunk in db_chunks]
            embeddings = generate_embeddings(texts_to_embed)

            qdrant_points = []
            es_actions = []

            for chunk, embedding in zip(db_chunks, embeddings):
                chunk_id_str = str(chunk.id)
                doc_id_str = str(doc.id)

                qdrant_points.append(
                    PointStruct(
                        id=chunk_id_str,
                        vector=embedding,
                        payload={
                            "document_id": doc_id_str,
                            "chunk_index": chunk.chunk_index,
                            "metadata_json": chunk.metadata_json,
                        },
                    )
                )

                es_actions.append(
                    {
                        "_op_type": "index",
                        "_index": settings.elastic_index_name,
                        "_id": chunk_id_str,
                        "document_id": doc_id_str,
                        "chunk_id": chunk_id_str,
                        "text_content": chunk.text_content,
                        "chunk_index": chunk.chunk_index,
                    }
                )

            if qdrant_points:
                await qdrant_client.upsert(
                    collection_name=settings.qdrant_collection_name,
                    points=qdrant_points,
                )

            if es_actions:
                await async_bulk(es_client, es_actions)

            doc.status = DocumentStatus.COMPLETED
            await db.commit()
            logger.info(f"Successfully indexed document {document_id}")

        except Exception as e:
            logger.exception(f"Failed to parse document {document_id}")
            doc.status = DocumentStatus.FAILED
            doc.error_message = str(e)
            await db.commit()


@celery_app.task(name="tasks.parse_document")
def parse_document_task(document_id: str) -> None:
    doc_uuid = uuid.UUID(document_id)
    asyncio.run(process_document_async(doc_uuid))
