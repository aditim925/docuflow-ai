
import asyncio
import logging
from uuid import UUID, uuid4
from app.messaging.schemas import DocumentIngestionEvent
from app.messaging.publisher import publish_ingestion_event

from fastapi import UploadFile
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, delete

from app.models.document import Document
from app.services.file_validation import validate_upload
from app.services.storage import upload_bytes, delete_object
from app.messaging.schemas import DocumentIngestionEvent
from app.messaging.publisher import publish_ingestion_event

logger = logging.getLogger(__name__)


async def upload_document(
    file: UploadFile,
    user_id: UUID,
    db: AsyncSession,
) -> Document:
    validated = await validate_upload(file)

    document_id = uuid4()
    object_key = f"documents/{user_id}/{document_id}"

    # 1. Upload the file to object storage
    await asyncio.to_thread(
        upload_bytes,
        validated.content,
        object_key,
        validated.content_type,
    )

    # 2. Save document metadata to PostgreSQL
    document = Document(
        id=document_id,
        user_id=user_id,
        filename=validated.filename,
        object_key=object_key,
        content_type=validated.content_type,
        file_size=validated.file_size,
        checksum=validated.checksum,
        status="UPLOADED",
    )

    try:
        db.add(document)
        await db.commit()
        await db.refresh(document)

    except Exception:
        await db.rollback()

        try:
            await asyncio.to_thread(delete_object, object_key)
        except Exception:
            logger.exception(
                "Failed to clean up storage object after database failure: %s",
                object_key,
            )

        raise

    # 3. Change status to QUEUED
    document.status = "QUEUED"
    try:
        await db.commit()

    except Exception:
        await db.rollback()
        logger.exception(
            "Failed to transition document to QUEUED: %s",
            document_id,
        )
        raise

    # 4. Create the ingestion event
    event = DocumentIngestionEvent.create(
        document_id=document.id,
        user_id=document.user_id,
        object_key=document.object_key,
        filename=document.filename,
        content_type=document.content_type,
        checksum=document.checksum,
    )

    # 5. Publish event to RabbitMQ
    try:
        await publish_ingestion_event(event)
        logger.info(
            "Document queued successfully for ingestion: %s",
            document_id,
        )

    except Exception:
        logger.exception(
            "Failed to publish ingestion event for document %s",
            document.id,
        )

        document.status = "FAILED"
        await db.commit()

    await db.refresh(document)
    # 6. Return the document
    return document

async def list_documents(
    user_id: UUID,
    db: AsyncSession,
    limit: int = 20,
    offset: int = 0,
) -> tuple[list[Document], int]:
    count_query = select(func.count(Document.id)).where(
        Document.user_id == user_id
    )

    total_result = await db.execute(count_query)
    total = total_result.scalar_one()

    documents_query = (
        select(Document)
        .where(Document.user_id == user_id)
        .order_by(Document.created_at.desc())
        .limit(limit)
        .offset(offset)
    )

    result = await db.execute(documents_query)
    documents = list(result.scalars().all())

    return documents, total

async def get_document(
    document_id: UUID,
    user_id: UUID,
    db: AsyncSession,
) -> Document | None:
    query = select(Document).where(
        Document.id == document_id,
        Document.user_id == user_id,
    )

    result = await db.execute(query)
    return result.scalar_one_or_none()

async def delete_document(
    document_id: UUID,
    user_id: UUID,
    db: AsyncSession,
) -> bool:
    document = await get_document(
        document_id=document_id,
        user_id=user_id,
        db=db,
    )

    if document is None:
        return False

    previous_status = document.status

    # Mark the document before touching object storage.
    document.status = "DELETING"
    await db.commit()

    try:
        await asyncio.to_thread(delete_object, document.object_key)
    except Exception:
        logger.exception(
            "Failed to delete document from storage: %s",
            document.object_key,
        )

        # Restore the previous status if storage deletion fails.
        document.status = previous_status
        await db.commit()
        raise

    try:
        await db.delete(document)
        await db.commit()
    except Exception:
        await db.rollback()
        logger.exception(
            "Storage object deleted, but database deletion failed for: %s",
            document_id,
        )
        raise

    return True
