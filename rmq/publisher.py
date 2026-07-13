"""
rmq/publisher.py
────────────────
Async RabbitMQ publisher.
Publishes JSON messages to the configured exchange.

Usage:
    from rmq.publisher import publish

    await publish("user.created", {"id": user_id, "email": email})
"""

import asyncio
import json
import logging
from datetime import datetime

import aio_pika

from core.config import settings

logger = logging.getLogger(__name__)

# Module-level connection — lazy-initialised, reused across calls
_connection: aio_pika.RobustConnection | None = None
_channel:    aio_pika.RobustChannel    | None = None
_lock = asyncio.Lock()


async def _get_channel() -> aio_pika.RobustChannel:
    """
    Returns a cached robust channel.
    Creates connection + channel on first call, reuses on subsequent calls.
    Thread-safe via asyncio.Lock.
    """
    global _connection, _channel

    async with _lock:
        if _connection is None or _connection.is_closed:
            logger.info("📤 Publisher: connecting to RabbitMQ")
            _connection = await aio_pika.connect_robust(settings.RABBITMQ_URL)

        if _channel is None or _channel.is_closed:
            _channel = await _connection.channel()
            logger.info("📤 Publisher: channel opened")

    return _channel


async def publish(
    event_type: str,
    data: dict,
    routing_key: str | None = None,
) -> None:
    """
    Publish a JSON message to the configured exchange.

    Args:
        event_type:  message type, e.g. "user.created" — added to body automatically
        data:        dict payload merged into the message body
        routing_key: override; defaults to settings.RMQ_ROUTING_KEY
    """
    body = {
        "event_type":  event_type,
        "published_at": datetime.utcnow().isoformat(),
        **data,
    }
    raw     = json.dumps(body).encode()
    rk      = routing_key or event_type   # use event_type as routing key by default
    channel = await _get_channel()

    exchange = await channel.declare_exchange(
        settings.RMQ_EXCHANGE,
        aio_pika.ExchangeType.TOPIC,
        durable=True,
    )

    await exchange.publish(
        aio_pika.Message(
            body=raw,
            content_type="application/json",
            delivery_mode=aio_pika.DeliveryMode.PERSISTENT,   # survives broker restart
        ),
        routing_key=rk,
    )
    logger.info(f"📤 Published event_type='{event_type}'  routing_key='{rk}'")


async def close() -> None:
    """Call during lifespan shutdown to cleanly close the publisher connection."""
    global _connection, _channel
    if _channel and not _channel.is_closed:
        await _channel.close()
    if _connection and not _connection.is_closed:
        await _connection.close()
    logger.info("📤 Publisher connection closed")
