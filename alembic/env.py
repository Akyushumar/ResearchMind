import asyncio
from logging.config import fileConfig

from alembic import context
from sqlalchemy.ext.asyncio import create_async_engine

from researchmind.config.settings import get_settings
from researchmind.models.base import Base
# Import all models so they are registered with Base
from researchmind.models.tables import (
    Amendment,
    ApplicabilityRule,
    Authority,
    Clause,
    ClauseRelationship,
    DocumentVersion,
    EvidenceChunk,
    IngestionJob,
    Jurisdiction,
    RegulatoryDocument,
)

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Interpret the config file for Python logging.
# This line sets up loggers basically.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata

def do_run_migrations(connection):
    context.configure(connection=connection, target_metadata=target_metadata)
    with context.begin_transaction():
        context.run_migrations()

async def run_async_migrations():
    """In this scenario we need to create an Engine
    and associate a connection with the context.
    """
    settings = get_settings()
    
    connectable = create_async_engine(
        settings.database_url,
        poolclass=None,
    )

    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)

    await connectable.dispose()

def run_migrations_online() -> None:
    """Run migrations in 'online' mode."""
    asyncio.run(run_async_migrations())

def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode."""
    settings = get_settings()
    context.configure(
        url=settings.database_url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()

if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
