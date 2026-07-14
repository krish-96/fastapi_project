"""
main.py
───────
Application entry point. Thin by design — all logic lives in submodules.

Structure:
    core/config.py       — pydantic-settings (reads .env)
    core/store.py        — in-memory stores (swap for DB/Redis)
    core/dependencies.py — FastAPI Depends() functions
    core/jobs.py         — background job dispatch (async + sync)
    models/              — Pydantic v2 request/response models
    routers/             — APIRouter modules (users, jobs, async_demo, health)
    rmq/consumer.py      — aio-pika consumer with handler registry
    rmq/health.py        — RabbitMQ health checker (state machine)
    rmq/publisher.py     — async RabbitMQ publisher (lazy connection)
"""

import asyncio
import logging
import time
from contextlib import asynccontextmanager

import httpx
from fastapi import FastAPI, Request, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from fastapi_app.core.store import active_connections, broadcast_ws
from fastapi_app.rmq import rmq_consumer, rmq_health_checker
from fastapi_app.rmq.publisher import close as close_publisher
from fastapi_app.routers import async_demo_router, health_router, jobs_router, users_router

# ─────────────────────────────────────────────
# Logging
# ─────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(lineno)s | %(message)s",
)
logger = logging.getLogger(__name__)


# ─────────────────────────────────────────────
# Custom exceptions
# ─────────────────────────────────────────────
class AppError(Exception):
    def __init__(self, message: str, code: int = 400):
        self.message = message
        self.code = code


# ─────────────────────────────────────────────
# Lifespan
# ─────────────────────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("🚀 Starting up")

    # Shared async HTTP client — one connection pool for the whole process
    app.state.http_client = httpx.AsyncClient(timeout=10.0)

    # RabbitMQ consumer — reconnects on broker restart
    # consumer_task = asyncio.create_task(rmq_consumer(), name="mq-consumer")
    consumer_task = asyncio.create_task(rmq_consumer(), name="mq-consumer")

    # RabbitMQ health checker — probes every RMQ_HEALTH_INTERVAL_SECS
    health_task = asyncio.create_task(rmq_health_checker(), name="mq-health")

    # Add this — surfaces silent task crashes immediately
    def _task_error_handler(task: asyncio.Task):
        if not task.cancelled() and task.exception():
            logger.error(f"💥 Task '{task.get_name()}' crashed: {task.exception()}")

    consumer_task.add_done_callback(_task_error_handler)
    health_task.add_done_callback(_task_error_handler)
    yield  # ← app runs here

    logger.info("🛑 Shutting down")

    for task in (consumer_task, health_task):
        task.cancel()
        try:
            await task
        except asyncio.CancelledError:
            pass

    await close_publisher()
    await app.state.http_client.aclose()

# =============================================
#           variables from .env
# =============================================
from core.config import settings

print("settings.APP_PORT", settings.APP_PORT)


# ─────────────────────────────────────────────
# App
# ─────────────────────────────────────────────
app = FastAPI(
    title="FastAPI Comprehensive Demo",
    version="1.0.0",
    lifespan=lifespan,
)


# ─────────────────────────────────────────────
# Middleware
# ─────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def request_timing_middleware(request: Request, call_next):
    start    = time.perf_counter()
    response = await call_next(request)
    elapsed  = (time.perf_counter() - start) * 1000
    logger.info(f"{request.method} {request.url.path} → {response.status_code} ({elapsed:.1f}ms)")
    response.headers["X-Process-Time-Ms"] = f"{elapsed:.1f}"
    return response


# ─────────────────────────────────────────────
# Exception handlers
# ─────────────────────────────────────────────
@app.exception_handler(AppError)
async def app_error_handler(request: Request, exc: AppError):
    return JSONResponse(status_code=exc.code, content={"error": exc.message})


@app.exception_handler(ValueError)
async def value_error_handler(request: Request, exc: ValueError):
    return JSONResponse(status_code=422, content={"error": str(exc)})


# ─────────────────────────────────────────────
# WebSocket
# ─────────────────────────────────────────────
@app.websocket("/ws")
async def websocket_endpoint(ws: WebSocket):
    """
    Real-time push for job completions and RabbitMQ state changes.
    Background jobs call broadcast_ws() on finish.
    """
    await ws.accept()
    active_connections.append(ws)
    try:
        while True:
            data = await ws.receive_text()
            await ws.send_text(f"echo: {data}")
    except WebSocketDisconnect:
        active_connections.remove(ws)


# ─────────────────────────────────────────────
# Routers
# ─────────────────────────────────────────────
app.include_router(health_router)
app.include_router(users_router)
app.include_router(jobs_router)
app.include_router(async_demo_router)


# main.py
if __name__ == "__main__":
    import uvicorn
    print(f"settings.APP_DEBUG: {settings.APP_DEBUG}")
    uvicorn.run(
        "main:app",
        host=settings.APP_HOST,
        port=settings.APP_PORT,
        reload=settings.APP_DEBUG,   # True in dev, False in prod
        workers=settings.APP_WORKERS,
    )
