# fastapi-demo

A production-structured FastAPI application covering every core concept:
DI, Pydantic v2, Lifespan, Middleware, Background Jobs (async + sync),
RabbitMQ consumer + publisher + health checker, WebSocket, and tests.

---

## Project structure

```
fastapi_app/
├── main.py                   lifespan · middleware · WebSocket · router registration
├── pyproject.toml            aio-pika · pydantic-settings · uvicorn · httpx
├── pytest.ini                asyncio_mode = auto
├── .env.example
│
├── core/
│   ├── config.py             pydantic-settings → reads .env (RMQ URL, intervals, prefetch)
│   ├── dependencies.py       get_http_client · get_current_user · require_admin
│   ├── jobs.py               dispatch_job → _async_job (gather) or _blocking_job (to_thread)
│   └── store.py              fake_users_db · job_status_store · broadcast_ws()
│
├── models/
│   ├── user.py               UserCreate (validators) · UserResponse (computed_field)
│   └── job.py                JobRequest (sync flag) · JobStatusResponse
│
├── routers/
│   ├── users.py              CRUD + publishes user.created / user.deleted to RMQ
│   ├── jobs.py               POST /jobs 202 · GET /jobs/{id} poll
│   ├── async_demo.py         gather · create_task · to_thread · sleep
│   └── health.py             GET /health · GET /health/rabbitmq
│
├── rmq/
│   ├── consumer.py           aio-pika loop · @register_handler · ack/nack · reconnect
│   ├── health.py             state machine: UNKNOWN → ALIVE/DEAD → RECOVERED
│   └── publisher.py          lazy robust connection · PERSISTENT delivery mode
│
└── tests/
    ├── conftest.py
    ├── test_users.py          Pydantic validators, CRUD, RMQ mocked
    ├── test_jobs.py           submit, poll, async + sync paths
    └── test_rmq_health.py     state transitions, no broker needed
```

---

## Quickstart

```bash
# 1. copy and edit config
cp .env.example .env

# 2. install
uv sync

# 3. run (RabbitMQ optional — app starts without it, health status = dead)
uv run uvicorn main:app --reload

# 4. open interactive docs
open http://localhost:8000/docs
```

## 📦 Project-Based Commands (Recommended)

Use these when managing your environment via pyproject.toml and uv.lock.

```bash
uv sync                      # Install all standard project dependencies
uv sync --all-groups         # Install everything including development & test tools
uv sync --clean              # Install valid dependencies and UNINSTALL everything else
uv add fastapi               # Add a package to pyproject.toml and install it instantly
uv remove fastapi            # Remove a package from pyproject.toml and uninstall it
uv run python main.py        # Automatically sync dependencies and run your script
```

---

## RabbitMQ

Start a local broker with Docker:

```bash
docker run -d --name rabbit \
  -p 5672:5672 -p 15672:15672 \
  rabbitmq:3-management
# management UI → http://localhost:15672  (guest/guest)
```

### Consumer — handler registry

Add handlers in `rmq/consumer.py` or any module imported at startup:

```python
from rmq.consumer import register_handler


@register_handler("order.placed")
async def handle_order(data: dict) -> None:
    ...
```

Message body must be JSON with `{"event_type": "...", ...}`.
Unknown event types are dropped (nack, no requeue).
Handler exceptions cause a nack with requeue=True (one retry).

### Publisher

```python
from rmq.publisher import publish

await publish("user.created", {"id": user_id, "email": email})
```

Uses a lazy robust connection — reconnects automatically.

### Health checker

Probes every `RMQ_HEALTH_INTERVAL_SECS` seconds.
Hook into state transitions in `rmq/health.py`:

```python
async def on_rabbitmq_down(state):
    await notify_slack(f"RabbitMQ DOWN at {state.last_dead}")


async def on_rabbitmq_recovered(state):
    await notify_slack(f"RabbitMQ back at {state.last_alive}")
```

Poll current state:

```bash
curl http://localhost:8000/health/rabbitmq
```

---

## Background jobs

```bash
# async job (asyncio.gather fan-out)
curl -X POST http://localhost:8000/jobs/ \
  -H "Content-Type: application/json" \
  -d '{"payload": {"key": "value"}, "sync": false}'

# sync/blocking job (runs in thread pool via to_thread)
curl -X POST http://localhost:8000/jobs/ \
  -d '{"payload": {"key": "value"}, "sync": true}'

# poll status
curl http://localhost:8000/jobs/<job_id>
```

---

## Tests

```bash
uv run pytest -v
```

RabbitMQ is mocked in all tests — no broker needed.

---

## Config reference (`.env`)

| Variable                   | Default                              | Description                       |
|----------------------------|--------------------------------------|-----------------------------------|
| `RABBITMQ_URL`             | `amqp://guest:guest@localhost:5672/` | broker connection string          |
| `RMQ_QUEUE`                | `task_queue`                         | consumer queue name               |
| `RMQ_EXCHANGE`             | `app_exchange`                       | topic exchange name               |
| `RMQ_ROUTING_KEY`          | `#`                                  | binding key (# = all topics)      |
| `RMQ_DLX`                  | `dlx`                                | dead-letter exchange name         |
| `RMQ_PREFETCH_COUNT`       | `10`                                 | max unacked messages per consumer |
| `RMQ_HEALTH_INTERVAL_SECS` | `10`                                 | health probe interval (seconds)   |
| `RMQ_PROBE_TIMEOUT_SECS`   | `3`                                  | TCP connect timeout for probe     |



Sample App Starting Logs:

```bash
(fastapi_project) fastapi_project|master⚡ ⇒ uv run uvicorn main:app --reload
INFO:     Will watch for changes in these directories: ['/home/krishna/Desktop/My_Space/fastapi_project']
INFO:     Uvicorn running on http://127.0.0.1:8000 (Press CTRL+C to quit)
INFO:     Started reloader process [291365] using WatchFiles
INFO:     Started server process [291367]
INFO:     Waiting for application startup.
2026-07-10 13:21:35,733 [INFO] main — 🚀 Starting up
2026-07-10 13:21:35,865 [INFO] rmq.consumer — 📨 RabbitMQ consumer starting
2026-07-10 13:21:35,865 [INFO] rmq.health — 🩺 RabbitMQ health checker started  interval=10.0s  probe_timeout=3.0s
INFO:     Application startup complete.
2026-07-10 13:21:35,872 [INFO] rmq.consumer — ✅ RabbitMQ consumer connected
2026-07-10 13:21:35,873 [INFO] rmq.health — 🟢 RabbitMQ RECOVERED at 2026-07-10T07:51:35.873565  (was dead since: None)
2026-07-10 13:21:35,879 [INFO] rmq.consumer — 📨 Consuming from queue='task_queue'  exchange='app_exchange'  routing_key='#'

^CINFO:     Shutting down
INFO:     Waiting for application shutdown.
2026-07-10 13:21:50,905 [INFO] main — 🛑 Shutting down
2026-07-10 13:21:50,907 [INFO] rmq.consumer — 📨 RabbitMQ consumer cancelled — shutting down
2026-07-10 13:21:50,907 [INFO] rmq.publisher — 📤 Publisher connection closed
INFO:     Application shutdown complete.
INFO:     Finished server process [291367]
INFO:     Stopping reloader process [291365]
```
