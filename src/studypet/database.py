import os
import sqlite3
from datetime import datetime, timedelta, timezone
from typing import Optional

from studypet.models import Pet, Task, TaskCreate

XP_PER_TASK = 25
XP_PER_LEVEL = 100


def get_db_path() -> str:
    return os.environ.get("STUDYPET_DB", "studypet.db")


def get_connection(db_path: Optional[str] = None) -> sqlite3.Connection:
    if db_path is None:
        db_path = get_db_path()
    conn = sqlite3.connect(db_path, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


def init_db(conn: sqlite3.Connection) -> None:
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS pet (
            id   INTEGER PRIMARY KEY CHECK (id = 1),
            name TEXT    NOT NULL DEFAULT 'Pixel',
            xp   INTEGER NOT NULL DEFAULT 0
        );

        CREATE TABLE IF NOT EXISTS tasks (
            id           INTEGER PRIMARY KEY AUTOINCREMENT,
            title        TEXT    NOT NULL,
            description  TEXT,
            completed    INTEGER NOT NULL DEFAULT 0,
            completed_at TEXT,
            created_at   TEXT    NOT NULL
        );

        INSERT OR IGNORE INTO pet (id, name, xp) VALUES (1, 'Pixel', 0);
    """)
    conn.commit()


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _compute_level(xp: int) -> int:
    return xp // XP_PER_LEVEL + 1


def _xp_to_next_level(xp: int) -> int:
    return XP_PER_LEVEL - (xp % XP_PER_LEVEL)


def _compute_mood(conn: sqlite3.Connection) -> str:
    cutoff = (datetime.now(timezone.utc) - timedelta(hours=24)).isoformat()
    row = conn.execute(
        "SELECT COUNT(*) AS cnt FROM tasks WHERE completed = 1 AND completed_at >= ?",
        (cutoff,),
    ).fetchone()
    count = row["cnt"]
    if count == 0:
        return "sad"
    if count <= 2:
        return "okay"
    if count <= 4:
        return "happy"
    return "ecstatic"


def _row_to_task(row: sqlite3.Row) -> Task:
    return Task(
        id=row["id"],
        title=row["title"],
        description=row["description"],
        completed=bool(row["completed"]),
        completed_at=row["completed_at"],
        created_at=row["created_at"],
    )


# ---------------------------------------------------------------------------
# Pet
# ---------------------------------------------------------------------------

def get_pet(conn: sqlite3.Connection) -> Pet:
    row = conn.execute("SELECT name, xp FROM pet WHERE id = 1").fetchone()
    xp = row["xp"]
    return Pet(
        name=row["name"],
        level=_compute_level(xp),
        xp=xp,
        mood=_compute_mood(conn),
        xp_to_next_level=_xp_to_next_level(xp),
    )


def _award_xp(conn: sqlite3.Connection, amount: int) -> Pet:
    conn.execute("UPDATE pet SET xp = xp + ? WHERE id = 1", (amount,))
    conn.commit()
    return get_pet(conn)


# ---------------------------------------------------------------------------
# Tasks
# ---------------------------------------------------------------------------

def create_task(conn: sqlite3.Connection, task_in: TaskCreate) -> Task:
    now = datetime.now(timezone.utc).isoformat()
    cur = conn.execute(
        "INSERT INTO tasks (title, description, completed, created_at) VALUES (?, ?, 0, ?)",
        (task_in.title, task_in.description, now),
    )
    conn.commit()
    task = get_task(conn, cur.lastrowid)
    assert task is not None
    return task


def get_task(conn: sqlite3.Connection, task_id: int) -> Optional[Task]:
    row = conn.execute("SELECT * FROM tasks WHERE id = ?", (task_id,)).fetchone()
    if row is None:
        return None
    return _row_to_task(row)


def list_tasks(conn: sqlite3.Connection, completed: Optional[bool] = None) -> list[Task]:
    if completed is None:
        rows = conn.execute(
            "SELECT * FROM tasks ORDER BY created_at DESC"
        ).fetchall()
    else:
        rows = conn.execute(
            "SELECT * FROM tasks WHERE completed = ? ORDER BY created_at DESC",
            (1 if completed else 0,),
        ).fetchall()
    return [_row_to_task(r) for r in rows]


def complete_task(conn: sqlite3.Connection, task_id: int) -> tuple[Task, Pet]:
    row = conn.execute("SELECT * FROM tasks WHERE id = ?", (task_id,)).fetchone()
    if row is None:
        raise ValueError(f"Task {task_id} not found")
    if row["completed"]:
        raise ValueError(f"Task {task_id} is already completed")

    now = datetime.now(timezone.utc).isoformat()
    conn.execute(
        "UPDATE tasks SET completed = 1, completed_at = ? WHERE id = ?",
        (now, task_id),
    )
    conn.commit()

    pet = _award_xp(conn, XP_PER_TASK)
    task = get_task(conn, task_id)
    assert task is not None
    return task, pet


def delete_task(conn: sqlite3.Connection, task_id: int) -> None:
    row = conn.execute("SELECT id FROM tasks WHERE id = ?", (task_id,)).fetchone()
    if row is None:
        raise ValueError(f"Task {task_id} not found")
    conn.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
    conn.commit()
