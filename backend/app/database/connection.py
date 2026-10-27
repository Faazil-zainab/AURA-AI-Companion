"""Small SQLite bootstrap used by the backend startup lifecycle."""

from __future__ import annotations

import sqlite3
from pathlib import Path


SCHEMA_PATH = Path(__file__).with_name("schema.sql")


def initialize_database(database_path: Path) -> None:
    """Create the local database and apply the checked-in base schema."""

    database_path.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(database_path) as connection:
        connection.executescript(SCHEMA_PATH.read_text(encoding="utf-8"))
