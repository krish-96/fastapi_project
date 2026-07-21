# core/database.py
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from core.config import settings

# ── Engine ────────────────────────────────────────────────────────────────────
# One engine per process — holds the connection pool
engine = create_async_engine(
    settings.DB_URL,          # mysql+aiomysql://user:pass@host/db
    pool_size=settings.DB_POOL_SIZE,             # base connections kept alive
    max_overflow=settings.MAX_OVERFLOW_SIZE,          # extra connections allowed under burst
    pool_pre_ping=True,       # checks connection health before use (detects stale)
    echo=settings.APP_DEBUG,  # logs SQL — True in dev, False in prod
)

# ── Session factory ───────────────────────────────────────────────────────────
# AsyncSessionLocal() creates a new session — called once per request
AsyncSessionLocal = async_sessionmaker(
    engine,
    expire_on_commit=False,   # don't expire objects after commit (async-safe)
    class_=AsyncSession,
)

# ── Dependency ────────────────────────────────────────────────────────────────
# Injected into routes via Depends(get_db)
# Opens session → yields → commits → closes (even on exception)
async def get_db() -> AsyncSession:
    async with AsyncSessionLocal() as session:
        yield session
        await session.commit()