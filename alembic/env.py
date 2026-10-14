"""Alembic environment: migrates the database configured in rxconfig.py."""

from logging.config import fileConfig

from reflex.config import get_config
from sqlmodel import SQLModel

from alembic import context
from app.models import engine

if context.config.config_file_name is not None:
    fileConfig(context.config.config_file_name)

# Autogenerate compares the database against every table defined in app.models.
target_metadata = SQLModel.metadata


def run_migrations_offline() -> None:
    """Emit the migration SQL without connecting to the database."""
    context.configure(
        url=get_config().db_url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Apply migrations over a live connection."""
    with engine().connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            # SQLite (local development) can only alter tables by recreating them.
            render_as_batch=connection.dialect.name == "sqlite",
        )
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
