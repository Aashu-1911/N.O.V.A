from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional, Sequence, Union

from database import get_connection


def _row_to_task(row):
    return {
        "id": row[0],
        "task_name": row[1],
        "date": row[2],
        "completed": bool(row[3]),
        "category": row[4],
        "priority": row[5],
        "created_at": row[6],
        "updated_at": row[7],
    }


def _fetch_task_by_identifier(cursor, task_identifier: Union[int, str]) -> Optional[Dict[str, Any]]:
    if isinstance(task_identifier, int):
        cursor.execute("SELECT * FROM tasks WHERE id = ?", (task_identifier,))
        row = cursor.fetchone()
        return _row_to_task(row) if row else None

    cursor.execute(
        """
        SELECT *
        FROM tasks
        WHERE LOWER(task_name) = LOWER(?)
        ORDER BY completed ASC, id DESC
        LIMIT 1
        """,
        (task_identifier,),
    )
    row = cursor.fetchone()
    return _row_to_task(row) if row else None


def add_task(
    task_name: str,
    date: Optional[str] = None,
    category: Optional[str] = None,
    priority: Optional[str] = None,
) -> Dict[str, Any]:
    if not task_name or not task_name.strip():
        raise ValueError("task_name is required")

    now = datetime.utcnow().isoformat(timespec="seconds")
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        INSERT INTO tasks (task_name, date, category, priority, completed, created_at, updated_at)
        VALUES (?, ?, ?, ?, 0, ?, ?)
        """,
        (task_name.strip(), date, category, priority, now, now),
    )

    conn.commit()
    task_id = cursor.lastrowid
    conn.close()

    return {
        "id": task_id,
        "task_name": task_name.strip(),
        "date": date,
        "category": category,
        "priority": priority,
        "completed": False,
        "created_at": now,
        "updated_at": now,
    }


def get_tasks(include_completed: bool = True) -> List[Dict[str, Any]]:
    conn = get_connection()
    cursor = conn.cursor()

    query = "SELECT * FROM tasks"
    if not include_completed:
        query += " WHERE completed = 0"
    query += " ORDER BY completed ASC, date IS NULL, date ASC, id DESC"

    cursor.execute(query)
    rows = cursor.fetchall()
    conn.close()

    return [_row_to_task(row) for row in rows]


def update_task(
    task_identifier: Union[int, str],
    *,
    task_name: Optional[str] = None,
    date: Optional[str] = None,
    category: Optional[str] = None,
    priority: Optional[str] = None,
    completed: Optional[bool] = None,
) -> Optional[Dict[str, Any]]:
    conn = get_connection()
    cursor = conn.cursor()

    task = _fetch_task_by_identifier(cursor, task_identifier)
    if not task:
        conn.close()
        return None

    updates = {
        "task_name": task_name,
        "date": date,
        "category": category,
        "priority": priority,
        "completed": None if completed is None else int(completed),
        "updated_at": datetime.utcnow().isoformat(timespec="seconds"),
    }
    assignments = []
    values = []
    for column_name, value in updates.items():
        if value is None:
            continue
        assignments.append(f"{column_name} = ?")
        values.append(value)

    if not assignments:
        conn.close()
        return task

    values.append(task["id"])
    cursor.execute(
        f"UPDATE tasks SET {', '.join(assignments)} WHERE id = ?",
        values,
    )
    conn.commit()

    updated_task = _fetch_task_by_identifier(cursor, task["id"])
    conn.close()
    return updated_task


def complete_task(task_identifier: Union[int, str]) -> Optional[Dict[str, Any]]:
    return update_task(task_identifier, completed=True)


def delete_task(task_identifier: Union[int, str]) -> bool:
    conn = get_connection()
    cursor = conn.cursor()
    task = _fetch_task_by_identifier(cursor, task_identifier)
    if not task:
        conn.close()
        return False

    cursor.execute("DELETE FROM tasks WHERE id = ?", (task["id"],))
    conn.commit()
    conn.close()
    return True


def get_task_stats() -> Dict[str, int]:
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) FROM tasks")
    total = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM tasks WHERE completed = 1")
    completed = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM tasks WHERE completed = 0")
    pending = cursor.fetchone()[0]

    conn.close()
    return {"total": total, "completed": completed, "pending": pending}


def find_task(task_identifier: Union[int, str]) -> Optional[Dict[str, Any]]:
    conn = get_connection()
    cursor = conn.cursor()
    task = _fetch_task_by_identifier(cursor, task_identifier)
    conn.close()
    return task