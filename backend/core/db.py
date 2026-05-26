from __future__ import annotations

import os
import pathlib
from typing import Optional

import aiosqlite


BACKEND_ROOT = pathlib.Path(__file__).resolve().parents[1]


def get_db_path() -> pathlib.Path:
    configured = os.getenv("GEOSCOPE_DB_PATH")
    if configured:
        return pathlib.Path(configured).expanduser().resolve()
    return (BACKEND_ROOT / "data" / "geoscope.db").resolve()


async def init_db(db_path: pathlib.Path) -> None:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    init_sql_path = BACKEND_ROOT / "init_db.sql"
    schema_sql = init_sql_path.read_text(encoding="utf-8")

    async with aiosqlite.connect(db_path.as_posix()) as conn:
        await conn.executescript(schema_sql)
        await conn.commit()


async def connect(db_path: Optional[pathlib.Path] = None) -> aiosqlite.Connection:
    path = (db_path or get_db_path()).as_posix()
    conn = await aiosqlite.connect(path)
    conn.row_factory = aiosqlite.Row
    return conn

