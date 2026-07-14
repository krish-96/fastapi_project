"""
routers/users.py
────────────────
User CRUD routes.
Publishes RabbitMQ events on create so downstream services can react.
"""

import uuid
import logging
from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, Depends, status

from core.dependencies import CurrentUserDep, require_admin
from core.store import fake_users_db
from models.user import UserCreate, UserResponse
from rmq.publisher import publish

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/users", tags=["Users"])


@router.post("/", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def create_user(body: UserCreate):
    user_id = str(uuid.uuid4())
    user = {
        "id":         user_id,
        "created_at": datetime.utcnow(),
        **body.model_dump(),
    }
    fake_users_db[user_id] = user

    # Publish event so consumer (handle_user_created) picks it up
    await publish("user.created", {"id": user_id, "email": body.email, "role": body.role})

    return user


@router.get("/", response_model=list[UserResponse])
async def list_users():
    return list(fake_users_db.values())


@router.get("/{user_id}", response_model=UserResponse)
async def get_user(user: CurrentUserDep):
    return user


@router.delete("/{user_id}", dependencies=[Depends(require_admin)])
async def delete_user(user_id: str):
    """Admin-only. Enforced via composed dependency — no value captured."""
    fake_users_db.pop(user_id, None)
    await publish("user.deleted", {"id": user_id})
    return {"deleted": user_id}
