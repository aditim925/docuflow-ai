

from uuid import UUID

from fastapi import APIRouter, Depends, File, Query, UploadFile, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.schemas.document import (
    DocumentUploadResponse,
    DocumentResponse,
    DocumentListResponse,
)

from app.services.document_upload import (
    upload_document,
    list_documents,
    get_document,
    delete_document,
)


import asyncio

from urllib.parse import quote

from botocore.exceptions import ClientError
from fastapi.responses import StreamingResponse

from app.services.storage import get_object

router = APIRouter(prefix="/documents", tags=["Documents"])


@router.post("/upload", response_model=DocumentUploadResponse, status_code=201)
async def upload_document_endpoint(
    user_id: UUID,
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
):
    document = await upload_document(
        file=file,
        user_id=user_id,
        db=db,
    )

    return document

@router.get("/", response_model=DocumentListResponse)
async def list_documents_endpoint(
    user_id: UUID,
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    db: AsyncSession = Depends(get_db),
):
    documents, total = await list_documents(
        user_id=user_id,
        db=db,
        limit=limit,
        offset=offset,
    )

    return DocumentListResponse(
        items=documents,
        total=total,
        limit=limit,
        offset=offset,
    )


@router.get("/{document_id}", response_model=DocumentResponse)
async def get_document_endpoint(
    document_id: UUID,
    user_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    document = await get_document(
        document_id=document_id,
        user_id=user_id,
        db=db,
    )

    if document is None:
        raise HTTPException(
            status_code=404,
            detail="Document not found",
        )

    return document


@router.get("/{document_id}/download")
async def download_document_endpoint(
    document_id: UUID,
    user_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    document = await get_document(
        document_id=document_id,
        user_id=user_id,
        db=db,
    )

    if document is None:
        raise HTTPException(
            status_code=404,
            detail="Document not found",
        )

    try:
        storage_response = await asyncio.to_thread(
            get_object,
            document.object_key,
        )
    except ClientError as exc:
        error_code = exc.response.get("Error", {}).get("Code", "")

        if error_code in ("404", "NoSuchKey", "NoSuchBucket", "NotFound"):
            raise HTTPException(
                status_code=404,
                detail="Stored document not found",
            ) from exc

        raise HTTPException(
            status_code=503,
            detail="Document storage is temporarily unavailable",
        ) from exc

    body = storage_response["Body"]

    def stream_file():
        try:
            while chunk := body.read(1024 * 1024):
                yield chunk
        finally:
            body.close()

    filename = quote(document.filename, safe="")

    return StreamingResponse(
        stream_file(),
        media_type=document.content_type,
        headers={
            "Content-Disposition": f"attachment; filename*=UTF-8''{filename}",
            "Content-Length": str(storage_response["ContentLength"]),
        },
    )

@router.delete("/{document_id}", status_code=204)
async def delete_document_endpoint(
    document_id: UUID,
    user_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    try:
        deleted = await delete_document(
            document_id=document_id,
            user_id=user_id,
            db=db,
        )
    except Exception as exc:
        raise HTTPException(
            status_code=503,
            detail="Unable to delete document",
        ) from exc

    if not deleted:
        raise HTTPException(
            status_code=404,
            detail="Document not found",
        )

    return None