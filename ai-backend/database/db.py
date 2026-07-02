import sqlite3
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DB_PATH = BASE_DIR / "data" / "nova.db"
DB_NAME = str(DB_PATH)


def get_connection():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    return sqlite3.connect(DB_PATH)


def _column_names(cursor, table_name):
    cursor.execute(f"PRAGMA table_info({table_name})")
    return {row[1] for row in cursor.fetchall()}


def init_db():
    conn = get_connection()

    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS tasks(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            task_name TEXT NOT NULL,
            date TEXT,
            category TEXT,
            priority TEXT,
            completed INTEGER DEFAULT 0,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)

    existing_columns = _column_names(cursor, "tasks")
    required_columns = {
        "category": "ALTER TABLE tasks ADD COLUMN category TEXT",
        "priority": "ALTER TABLE tasks ADD COLUMN priority TEXT",
        "created_at": "ALTER TABLE tasks ADD COLUMN created_at TEXT",
        "updated_at": "ALTER TABLE tasks ADD COLUMN updated_at TEXT",
    }

    for column_name, statement in required_columns.items():
        if column_name not in existing_columns:
            cursor.execute(statement)

    conn.commit()
    conn.close()