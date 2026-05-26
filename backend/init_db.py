from __future__ import annotations

import pathlib
import sqlite3


ROOT = pathlib.Path(__file__).resolve().parent
DB_PATH = pathlib.Path(
    (ROOT / "data" / "geoscope.db").as_posix()
)


def _ensure_columns(conn: sqlite3.Connection, table: str, columns: dict[str, str]) -> None:
    cur = conn.execute(f"PRAGMA table_info({table})")
    rows = cur.fetchall()
    existing = {r[1] for r in rows}
    for name, ddl in columns.items():
        if name in existing:
            continue
        conn.execute(f"ALTER TABLE {table} ADD COLUMN {name} {ddl}")


def main() -> None:
    (ROOT / "data").mkdir(parents=True, exist_ok=True)
    sql_path = ROOT / "init_db.sql"
    with sql_path.open("r", encoding="utf-8") as f:
        schema_sql = f.read()

    conn = sqlite3.connect(DB_PATH)
    try:
        # init_db.sql 里包含 CREATE INDEX（可能引用新字段）。
        # 对已有旧 DB：CREATE TABLE IF NOT EXISTS 不会补列，直接建索引会失败。
        if "\n-- 索引" in schema_sql:
            before, after = schema_sql.split("\n-- 索引", 1)
            conn.executescript(before)
            _ensure_columns(
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
            conn.execute("UPDATE analyses SET client_id='public' WHERE client_id IS NULL")
            conn.executescript("-- 索引" + after)
        else:
            conn.executescript(schema_sql)
        conn.commit()
    finally:
        conn.close()

    print(f"DB initialized at: {DB_PATH}")


if __name__ == "__main__":
    main()
