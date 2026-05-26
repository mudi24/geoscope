from __future__ import annotations

import pathlib
import sqlite3


ROOT = pathlib.Path(__file__).resolve().parent
DB_PATH = pathlib.Path(
    (ROOT / "data" / "geoscope.db").as_posix()
)


def main() -> None:
    (ROOT / "data").mkdir(parents=True, exist_ok=True)
    sql_path = ROOT / "init_db.sql"
    with sql_path.open("r", encoding="utf-8") as f:
        schema_sql = f.read()

    conn = sqlite3.connect(DB_PATH)
    try:
        conn.executescript(schema_sql)
        conn.commit()
    finally:
        conn.close()

    print(f"DB initialized at: {DB_PATH}")


if __name__ == "__main__":
    main()

