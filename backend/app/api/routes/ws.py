"""WebSocket gateway — bridges Kafka feedback topic to connected clients."""

import asyncio
import json
import logging

from aiokafka import AIOKafkaConsumer
from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from app.config import settings

logger = logging.getLogger(__name__)
router = APIRouter(tags=["websocket"])

# interview_id → set of connected WebSocket clients
_connections: dict[str, set[WebSocket]] = {}


async def _broadcast(interview_id: str, message: dict) -> None:
    dead = set()
    for ws in _connections.get(interview_id, set()):
        try:
            await ws.send_json(message)
        except Exception:
            dead.add(ws)
    for ws in dead:
        _connections[interview_id].discard(ws)


async def run_ws_feedback_consumer() -> None:
    """Background task: consumes feedback + completed topics and broadcasts to WS clients."""
    consumer = AIOKafkaConsumer(
        settings.KAFKA_TOPIC_FEEDBACK,
        settings.KAFKA_TOPIC_COMPLETED,
        bootstrap_servers=settings.KAFKA_BOOTSTRAP_SERVERS,
        group_id=f"{settings.KAFKA_GROUP_ID}-ws",
        value_deserializer=lambda v: json.loads(v.decode("utf-8")),
        auto_offset_reset="latest",
    )
    await consumer.start()
    logger.info("WS feedback consumer started")
    try:
        async for msg in consumer:
            payload = msg.value
            interview_id = payload.get("interview_id")
            if interview_id and interview_id in _connections:
                await _broadcast(interview_id, payload)
    finally:
        await consumer.stop()


@router.websocket("/ws/interviews/{interview_id}")
async def interview_ws(interview_id: str, websocket: WebSocket):
    await websocket.accept()
    _connections.setdefault(interview_id, set()).add(websocket)
    logger.info("WS client connected: interview_id=%s", interview_id)
    try:
        while True:
            await asyncio.sleep(30)
            await websocket.send_json({"type": "ping"})
    except (WebSocketDisconnect, RuntimeError):
        pass
    finally:
        _connections[interview_id].discard(websocket)
        logger.info("WS client disconnected: interview_id=%s", interview_id)
