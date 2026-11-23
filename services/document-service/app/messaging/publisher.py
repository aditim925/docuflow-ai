import logging

import aio_pika

from app.messaging.rabbitmq import rabbitmq_manager
from app.messaging.schemas import DocumentIngestionEvent

logger = logging.getLogger(__name__)


async def publish_ingestion_event(
    event: DocumentIngestionEvent,
) -> None:
    if rabbitmq_manager.exchange is None:
        raise RuntimeError("RabbitMQ is not connected")

    message = aio_pika.Message(
        body=event.model_dump_json().encode("utf-8"),
        content_type="application/json",
        content_encoding="utf-8",
        message_id=str(event.event_id),
        correlation_id=str(event.document_id),
        type=event.event_type,
        delivery_mode=aio_pika.DeliveryMode.PERSISTENT,
    )

    await rabbitmq_manager.exchange.publish(
        message,
        routing_key="document.ingestion.requested",
        mandatory=True,
    )

    logger.info(
        "Published ingestion event for document %s",
        event.document_id,
    )