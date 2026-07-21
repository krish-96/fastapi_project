"""
core/config.py
──────────────
Single source of truth for all config.
Reads from environment variables (or .env file).
"""

from typing import Optional


from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field, model_validator, fields


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",  # ← was "forbid"
    )

    # Test variables
    # core/config.py
    APP_HOST: str = "0.0.0.0"
    APP_PORT: int = 8000
    APP_DEBUG: bool = False
    APP_WORKERS: int = 1  # >1 disables reload


    # Database configuration
    # DB_URL: str = Field()  # required — no default, crashes loudly if missing
    # Set defaults to None so Pydantic doesn't crash before the validator runs
    DB_URL: Optional[str] = Field(default=None, description="The primary DB connection string")
    DB_HOST: Optional[str] = Field(default=None)
    # DB_PORT: Optional[int] = Field(default=3306)  # Default MySQL port
    DB_PORT: Optional[int] = Field(default=None)  # To raise exception if port is missing from .env
    DB_USER: Optional[str] = Field(default=None)
    DB_PASSWORD: Optional[str] = Field(default=None)
    DB_NAME: Optional[str] = Field(default=None)  # Corrected type from int to str

    DB_POOL_SIZE: int = Field(default=10)
    MAX_OVERFLOW_SIZE: int = Field(default=20)

    # ── RabbitMQ ──────────────────────────────
    RABBITMQ_URL: str = Field(default="amqp://guest:guest@localhost:5672/")
    RMQ_QUEUE: str = Field(default="task_queue")
    RMQ_EXCHANGE: str = Field(default="app_exchange")
    RMQ_ROUTING_KEY: str = Field(default="#")  # match all topics
    RMQ_DLX: str = Field(default="dlx")  # dead-letter exchange
    RMQ_PREFETCH_COUNT: int = Field(default=10)

    # ── Concurrency control ────────────────────
    # Rule: RMQ_MAX_CONCURRENT_TASKS >= RMQ_PREFETCH_COUNT
    # prefetch_count  → broker delivers at most N unacked messages
    # max_concurrent  → app processes at most N messages at once (semaphore)
    RMQ_MAX_CONCURRENT_TASKS: int = Field(default=50)  # semaphore cap

    # ── Shutdown ───────────────────────────────
    RMQ_DRAIN_TIMEOUT_SECS: float = Field(default=30.0)  # wait up to N secs for tasks on shutdown

    # ── Health checker ─────────────────────────
    # RMQ_HEALTH_INTERVAL_SECS:  float = 10.0   # probe every N seconds
    RMQ_HEALTH_INTERVAL_SECS: float = Field(default=2.0)  # probe every N seconds
    RMQ_PROBE_TIMEOUT_SECS: float = Field(default=3.0)  # TCP connect timeout
    RMQ_HEALTH_INITIAL_DELAY_SECS: float = Field(default=5.0)
    RMQ_MAX_RETRIES: int = Field(default=3)

    RMQ_INITIAL_HEALTH_CHECK_TYPE: Optional[str] = Field(default='poll')

    CREATE_QUEUE_IF_DELETED: str = Field(default=False)

    LOG_LEVEL: str = Field(default="INFO")


    @model_validator(mode="after")
    def validate_or_build_db_url(self) -> "Settings":
        # Scenario A: DB_URL is already provided in environment/.env
        if self.DB_URL:
            print(f"DB_URL: {self.DB_URL} Exists So returning immediately")
            return self

        # Scenario B: DB_URL is missing, so we MUST have the individual parts
        required_fields = {
            "DB_HOST": self.DB_HOST,
            "DB_USER": self.DB_USER,
            "DB_PASSWORD": self.DB_PASSWORD,
            "DB_NAME": self.DB_NAME,
        }

        # Check if any required component is missing
        missing = [key for key, val in required_fields.items() if val is None]
        if missing:
            raise ValueError(
                f"Missing environment variables. Provide either 'DB_URL' or "
                f"all individual components. Missing: {', '.join(missing)}"
            )

        # Build DB_URL dynamically
        self.DB_URL = f"mysql+pymysql://{self.DB_USER}:{self.DB_PASSWORD}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"
        return self


settings = Settings()
