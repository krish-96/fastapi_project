"""
routers/health.py
─────────────────
Liveness + RabbitMQ health endpoints.
"""

from datetime import datetime

from fastapi import APIRouter

from rmq.health import rmq_health

router = APIRouter(prefix="/health", tags=["Meta"])


@router.get("/")
async def health():
    return {"status": "ok", "time": datetime.utcnow().isoformat()}


@router.get("/rabbitmq")
async def rabbitmq_health():
    """
    Current RabbitMQ health state.

    status values:
      unknown   — app just started, no probe yet
      alive     — last probe succeeded
      dead      — last probe failed (see consecutive_failures)
      recovered — came back after being dead
    """
    return rmq_health.to_dict()