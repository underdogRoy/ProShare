import logging
import time
from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.exc import OperationalError

logger = logging.getLogger(__name__)


def _prepare_sqlite_path(database_url: str) -> None:
    prefix = "sqlite:///"
    if not database_url.startswith(prefix):
        return

    db_path = database_url[len(prefix) :]
    if not db_path or db_path == ":memory:":
        return

    Path(db_path).expanduser().parent.mkdir(parents=True, exist_ok=True)


def _normalize_db_url(url: str) -> str:
    # Render provides postgres:// or postgresql://; psycopg v3 needs postgresql+psycopg://
    if url.startswith("postgres://"):
        return "postgresql+psycopg://" + url[len("postgres://"):]
    if url.startswith("postgresql://"):
        return "postgresql+psycopg://" + url[len("postgresql://"):]
    return url


def build_engine(database_url: str, retries: int = 15, retry_delay: float = 3.0):
    if database_url.startswith("sqlite"):
        _prepare_sqlite_path(database_url)
        return create_engine(database_url, connect_args={"check_same_thread": False})

    engine = create_engine(_normalize_db_url(database_url))
    for attempt in range(retries):
        try:
            with engine.connect():
                return engine
        except OperationalError:
            if attempt < retries - 1:
                logger.warning("Database not ready, retrying in %.0fs (%d/%d)...", retry_delay, attempt + 1, retries)
                time.sleep(retry_delay)
            else:
                raise
    return engine
