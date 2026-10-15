"""Reflex configuration.

Deployment settings come from environment variables, so the same code runs
locally and on Railway:

- DATABASE_URL: Postgres connection string (`${{Postgres.DATABASE_URL}}` on
  Railway). Without it the app uses a local SQLite file.
- REFLEX_REDIS_URL: Redis that stores state shared by every backend worker.
"""

import os

import reflex as rx


def database_url() -> str:
    """Build the SQLAlchemy URL from DATABASE_URL.

    Returns:
        The URL with the psycopg driver selected, or a local SQLite URL.
    """
    url = os.environ.get("DATABASE_URL", "")
    for scheme in ("postgres://", "postgresql://"):
        if url.startswith(scheme):
            return "postgresql+psycopg://" + url.removeprefix(scheme)
    return url or "sqlite:///reflex.db"


config = rx.Config(
    app_name="app",
    db_url=database_url(),
    plugins=[rx.plugins.RadixThemesPlugin(theme=rx.theme(accent_color="violet"))],
    disable_plugins=[rx.plugins.SitemapPlugin],
)
