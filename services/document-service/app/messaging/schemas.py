from datetime import datetime, timezone
from uuid import UUID, uuid4

from pydantic import BaseModel


class DocumentIngestionEvent(BaseModel):
    event_id: UUID
    event_type: str = "document.ingestion.requested"

    document_id: UUID
    user_id: UUID

    object_key: str
    filename: str
    content_type: str
    checksum: str

    created_at: datetime
    version: int = 1

    @classmethod
    def create(
        cls,
        document_id: UUID,
        user_id: UUID,
        object_key: str,
        filename: str,
        content_type: str,
        checksum: str,
    ) -> "DocumentIngestionEvent":
        return cls(
            event_id=uuid4(),
            document_id=document_id,
            user_id=user_id,
            object_key=object_key,
            filename=filename,
            content_type=content_type,
            checksum=checksum,
            created_at=datetime.now(timezone.utc),
        )