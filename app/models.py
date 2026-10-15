"""Database tables and the engine shared by event handlers and migrations."""

from datetime import datetime
from functools import cache

import sqlalchemy as sa
import sqlmodel
from reflex.config import get_config

MAX_NAME_LENGTH = 60
MAX_MESSAGE_LENGTH = 500


class Entry(sqlmodel.SQLModel, table=True):
    """A guestbook entry."""

    id: int | None = sqlmodel.Field(default=None, primary_key=True)
    name: str = sqlmodel.Field(max_length=MAX_NAME_LENGTH)
    message: str = sqlmodel.Field(max_length=MAX_MESSAGE_LENGTH)
    created_at: datetime | None = sqlmodel.Field(
        default=None,
        sa_column=sa.Column(
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
            index=True,
        ),
    )


@cache
def engine() -> sa.Engine:
    """Create the database engine once per process.

    Returns:
        The engine for the configured `db_url` (`REFLEX_DB_URL` overrides it).
    """
    # pool_pre_ping replaces connections the database closed while idle.
    return sqlmodel.create_engine(get_config().db_url, pool_pre_ping=True)
