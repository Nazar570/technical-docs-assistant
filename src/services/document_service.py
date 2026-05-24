import hashlib
import uuid
from pathlib import Path

import aiofiles
from fastapi import HTTPException, UploadFile, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.config import settings
from src.models.document import Document, DocumentStatus
from src.schemas.document import DocumentResponse


async def compute_file_hash(file: UploadFile) -> str:
    sha256 = hashlib.sha256()
    await file.seek(0)

    while chunk := await file.read(8192):
        sha256.update(chunk)

    await file.seek(0)
    return sha256.hexdigest()


async def upload_and_record_document(
    db: AsyncSession, file: UploadFile
) -> DocumentResponse:
    file_hash = await compute_file_hash(file)

    stmt = select(Document).where(Document.content_hash == file_hash)
    result = await db.execute(stmt)
    existing_doc = result.scalar_one_or_none()

    if existing_doc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Document already exists with ID: {existing_doc.id}",
        )

    doc_id = uuid.uuid4()
    safe_filename = f"{doc_id}_{file.filename}"
    file_path = Path(settings.storage_dir) / safe_filename

    async with aiofiles.open(file_path, "wb") as out_file:
        while chunk := await file.read(8192):
            await out_file.write(chunk)

    new_doc = Document(
        id=doc_id,
        filename=file.filename or "unknown",
        content_hash=file_hash,
        status=DocumentStatus.PENDING,
    )
    db.add(new_doc)
    await db.commit()
    await db.refresh(new_doc)

    return DocumentResponse.model_validate(new_doc)
