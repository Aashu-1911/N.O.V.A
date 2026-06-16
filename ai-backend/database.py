import sqlite3

DB_NAME = "jarvis.db"


def get_connection():
    return sqlite3.connect(DB_NAME)


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