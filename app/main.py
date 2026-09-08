"""
BIMVORA FastAPI application.

Startup order:
  1. Run Alembic migrations (sync, via psycopg2 — avoids MissingGreenlet)
  2. Start FastAPI app with async SQLAlchemy engine (asyncpg)
"""
import asyncio
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)-8s %(name)s  %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("bimvora")


def _run_migrations() -> None:
    """
    Run Alembic migrations using the SYNC psycopg2 engine.

    CRITICAL: This MUST be called before the asyncpg engine connects.
    Never mix asyncpg and Alembic — that is the root cause of MissingGreenlet.
    """
    from alembic.config import Config
    from alembic import command

    logger.info("Running database migrations...")
    alembic_cfg = Config("alembic.ini")
    # env.py picks up settings.sync_database_url automatically
    command.upgrade(alembic_cfg, "head")
    logger.info("Migrations complete.")


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Migrations run synchronously in a thread pool to avoid blocking the event loop
    loop = asyncio.get_event_loop()
    await loop.run_in_executor(None, _run_migrations)

    yield  # App is running

    # Cleanup: dispose the async engine connection pool
    from app.database import engine
    await engine.dispose()
    logger.info("Database engine disposed.")


app = FastAPI(
    title="BIMVORA API",
    description="Backend for bimvora.com — Professional Revit Families Store",
    version="1.0.0",
    lifespan=lifespan,
    # Disable Swagger in production (security best practice)
    docs_url="/docs" if settings.debug else None,
    redoc_url="/redoc" if settings.debug else None,
    openapi_url="/openapi.json" if settings.debug else None,
)

# CORS — only allow requests from the frontend domain
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        settings.frontend_url,
        "http://localhost:3000",  # Local development
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Rate limiting (slowapi)
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Mount routers
from app.routers import health, products, categories, orders, webhooks, tracking, downloads, newsletter

app.include_router(health.router, tags=["health"])
app.include_router(products.router, prefix="/products", tags=["products"])
app.include_router(categories.router, prefix="/categories", tags=["categories"])
app.include_router(orders.router, prefix="/orders", tags=["orders"])
app.include_router(webhooks.router, prefix="/webhooks", tags=["webhooks"])
app.include_router(tracking.router, prefix="/tracking", tags=["tracking"])
app.include_router(downloads.router, prefix="/downloads", tags=["downloads"])
app.include_router(newsletter.router, prefix="/newsletter", tags=["newsletter"])


@app.get("/")
async def root():
    return {"name": "BIMVORA API", "version": "1.0.0", "status": "ok"}
