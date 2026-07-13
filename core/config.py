"""
core/config.py
──────────────
Single source of truth for all config.
Reads from environment variables (or .env file).
"""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",  # ← was "forbid"

    )

    # ── RabbitMQ ──────────────────────────────
    RABBITMQ_URL:              str   = "amqp://guest:guest@localhost:5672/"
    RMQ_QUEUE:                 str   = "task_queue"
    RMQ_EXCHANGE:              str   = "app_exchange"
    RMQ_ROUTING_KEY:           str   = "#"            # match all topics
    RMQ_DLX:                   str   = "dlx"          # dead-letter exchange
    RMQ_PREFETCH_COUNT:        int   = 10

    # ── Concurrency control ────────────────────
    # Rule: RMQ_MAX_CONCURRENT_TASKS >= RMQ_PREFETCH_COUNT
    # prefetch_count  → broker delivers at most N unacked messages
    # max_concurrent  → app processes at most N messages at once (semaphore)
    RMQ_MAX_CONCURRENT_TASKS:  int   = 50     # semaphore cap

    # ── Shutdown ───────────────────────────────
    RMQ_DRAIN_TIMEOUT_SECS:    float = 30.0   # wait up to N secs for tasks on shutdown

    # ── Health checker ─────────────────────────
    # RMQ_HEALTH_INTERVAL_SECS:  float = 10.0   # probe every N seconds
    RMQ_HEALTH_INTERVAL_SECS:  float = 2.0   # probe every N seconds
    RMQ_PROBE_TIMEOUT_SECS:    float = 3.0    # TCP connect timeout
    RMQ_HEALTH_INITIAL_DELAY_SECS: float = 5.0

    # Test variables
    # core/config.py
    APP_HOST: str = "0.0.0.0"
    APP_PORT: int = 8000
    APP_DEBUG: bool = False
    APP_WORKERS: int = 1  # >1 disables reload




settings = Settings()