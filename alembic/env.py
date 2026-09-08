"""
Alembic migration environment.

KEY FIX for sqlalchemy.exc.MissingGreenlet:
  Alembic runs in a sync context. It MUST use a SYNCHRONOUS engine (psycopg2),
  NOT the async engine (asyncpg) used by the FastAPI app.

  settings.sync_database_url automatically swaps postgresql+asyncpg:// 
  with postgresql+psycopg2:// so both work from the same DATABASE_URL env var.
"""
from logging.config import fileConfig

from sqlalchemy import engine_from_config, pool
from alembic import context

from app.config import settings
from app.database import Base

# Import all models so Alembic autogenerate can detect them
import app.models  # noqa: F401

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


def run_migrations_offline() -> None:
    """Run migrations without a DB connection (generates SQL script)."""
    url = settings.sync_database_url  # <-- sync URL
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """
    Run migrations with a SYNCHRONOUS engine.
    Using psycopg2 (sync) here — asyncpg would cause MissingGreenlet.
    """
    configuration = config.get_section(config.config_ini_section, {})
    # Override the URL from alembic.ini with our sync URL
    configuration["sqlalchemy.url"] = settings.sync_database_url

    connectable = engine_from_config(
        configuration,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,  # No connection pooling needed for migrations
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,       # Detect column type changes
            compare_server_default=True,
        )
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
