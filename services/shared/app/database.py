from pathlib import Path

from sqlalchemy import create_engine


def _prepare_sqlite_path(database_url: str) -> None:
    prefix = "sqlite:///"
    if not database_url.startswith(prefix):
        return

    db_path = database_url[len(prefix) :]
    if not db_path or db_path == ":memory:":
        return

    Path(db_path).expanduser().parent.mkdir(parents=True, exist_ok=True)


def build_engine(database_url: str):
    if database_url.startswith("sqlite"):
        _prepare_sqlite_path(database_url)
        return create_engine(database_url, connect_args={"check_same_thread": False})
    return create_engine(database_url)
