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
        await _ensure_columns(
            conn,
            "analyses",
            {
                "client_id": "TEXT",
                "status": "TEXT DEFAULT 'done'",
                "error": "TEXT",
                "updated_at": "TIMESTAMP DEFAULT CURRENT_TIMESTAMP",
                "score_evidence": "TEXT",
            },
        )
        # Backfill for older DBs before client isolation existed
        await conn.execute("UPDATE analyses SET client_id='public' WHERE client_id IS NULL")
        await conn.commit()


async def _ensure_columns(conn: aiosqlite.Connection, table: str, columns: dict[str, str]) -> None:
    cur = await conn.execute(f"PRAGMA table_info({table})")
    rows = await cur.fetchall()
    existing = {r[1] for r in rows}
    for name, ddl in columns.items():
        if name in existing:
            continue
        await conn.execute(f"ALTER TABLE {table} ADD COLUMN {name} {ddl}")


async def connect(db_path: Optional[pathlib.Path] = None) -> aiosqlite.Connection:
    path = (db_path or get_db_path()).as_posix()
    conn = await aiosqlite.connect(path)
    conn.row_factory = aiosqlite.Row
    return conn
