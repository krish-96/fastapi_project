"""
tests/test_users.py
────────────────────
Tests for user CRUD endpoints.
Uses httpx.AsyncClient with FastAPI's ASGI transport — no live server needed.
RabbitMQ publisher is mocked so tests don't need a broker.
"""

import pytest
from httpx import ASGITransport, AsyncClient
from unittest.mock import AsyncMock, patch

from main import app


@pytest.fixture
async def client():
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:
        yield ac


# ── patch publisher so no RabbitMQ needed in tests ───────────────────────────
@pytest.fixture(autouse=True)
def mock_publish(monkeypatch):
    monkeypatch.setattr("routers.users.publish", AsyncMock())


# ─────────────────────────────────────────────
# Create
# ─────────────────────────────────────────────
@pytest.mark.asyncio
async def test_create_user_success(client):
    resp = await client.post("/users/", json={
        "name": "Alice", "email": "Alice@Example.com", "age": 30, "role": "viewer"
    })
    assert resp.status_code == 201
    data = resp.json()
    assert data["email"] == "alice@example.com"   # lowercased by validator
    assert data["is_admin"] is False               # computed_field


@pytest.mark.asyncio
async def test_create_user_invalid_email(client):
    resp = await client.post("/users/", json={
        "name": "Bob", "email": "not-an-email", "age": 25
    })
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_create_user_negative_age(client):
    resp = await client.post("/users/", json={
        "name": "Carol", "email": "carol@x.com", "age": -1
    })
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_admin_must_be_adult(client):
    resp = await client.post("/users/", json={
        "name": "Dan", "email": "dan@x.com", "age": 16, "role": "admin"
    })
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_admin_computed_field(client):
    resp = await client.post("/users/", json={
        "name": "Eve", "email": "eve@x.com", "age": 25, "role": "admin"
    })
    assert resp.status_code == 201
    assert resp.json()["is_admin"] is True


# ─────────────────────────────────────────────
# List + Get
# ─────────────────────────────────────────────
@pytest.mark.asyncio
async def test_list_users(client):
    await client.post("/users/", json={"name": "X", "email": "x@x.com", "age": 20})
    resp = await client.get("/users/")
    assert resp.status_code == 200
    assert len(resp.json()) >= 1


@pytest.mark.asyncio
async def test_get_user_not_found(client):
    resp = await client.get("/users/nonexistent-id")
    assert resp.status_code == 404
