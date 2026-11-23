import logging

import aio_pika
from aio_pika import ExchangeType

from app.core.config import settings

logger = logging.getLogger(__name__)


class RabbitMQManager:
    def __init__(self):
        self.connection = None
        self.channel = None
        self.exchange = None
        self.queue = None

    async def connect(self):
        if self.connection and not self.connection.is_closed:
            return

        logger.info("Connecting to RabbitMQ...")

        self.connection = await aio_pika.connect_robust(
            settings.rabbitmq_url
        )

        self.channel = await self.connection.channel()

        await self.channel.set_qos(prefetch_count=10)

        self.exchange = await self.channel.declare_exchange(
            "docuflow.exchange",
            ExchangeType.DIRECT,
            durable=True,
        )

        self.queue = await self.channel.declare_queue(
            "document.ingestion.queue",
            durable=True,
        )

        await self.queue.bind(
            self.exchange,
            routing_key="document.ingestion.requested",
        )

        logger.info("RabbitMQ connection established successfully")

    async def close(self):
        if self.connection and not self.connection.is_closed:
            await self.connection.close()
            logger.info("RabbitMQ connection closed")


rabbitmq_manager = RabbitMQManager()