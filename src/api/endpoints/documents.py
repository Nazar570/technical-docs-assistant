from fastapi import APIRouter, Depends, File, UploadFile
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database import get_db
from src.models.document import Document
from src.schemas.document import DocumentResponse
from src.services import document_service
from src.worker.tasks import parse_document_task

router = APIRouter()


@router.post("/", response_model=DocumentResponse, status_code=201)
async def upload_document(
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
) -> DocumentResponse:
    new_doc = await document_service.upload_and_record_document(db, file)

    parse_document_task.delay(str(new_doc.id))

    return new_doc


@router.get("/", response_model=list[DocumentResponse])
async def list_documents(
    limit: int = 50, db: AsyncSession = Depends(get_db)
) -> list[DocumentResponse]:
    """
    Retrieve a list of all uploaded documents and their processing status.
    """
    stmt = select(Document).order_by(Document.created_at.desc()).limit(limit)
    result = await db.execute(stmt)
    documents = result.scalars().all()

    return list(documents)
