"""
core/store.py
─────────────
Shared in-memory stores.
Replace fake_users_db with an async SQLAlchemy session factory.
Replace job_status_store with a Redis or DB-backed store for multi-process deployments.
"""

from fastapi import WebSocket

# ── Users ──────────────────────────────────────────────────────────────────────
fake_users_db: dict[str, dict] = {}

# ── Background jobs ────────────────────────────────────────────────────────────
job_status_store: dict[str, dict] = {}

# ── WebSocket connections ──────────────────────────────────────────────────────
active_connections: list[WebSocket] = []


async def broadcast_ws(message: str) -> None:
    """Push a text message to all connected WebSocket clients."""
    dead = []
    for ws in active_connections:
        try:
            await ws.send_text(message)
        except Exception:
            dead.append(ws)
    for ws in dead:
        active_connections.remove(ws)
