"""
models/job.py
─────────────
Pydantic v2 models for the background Job domain.
"""

from datetime import datetime
from typing import Any

from pydantic import BaseModel


class JobRequest(BaseModel):
    payload: dict[str, Any]
    sync: bool = False   # True → run via asyncio.to_thread (blocking workload)


class JobStatusResponse(BaseModel):
    job_id: str
    status: str          # pending | running | done | failed
    result: Any = None
    started_at: datetime | None = None
    finished_at: datetime | None = None
