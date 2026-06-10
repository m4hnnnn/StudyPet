import os
import sqlite3
from datetime import datetime, timedelta, timezone
from typing import Optional

from studypet.models import Pet, Stats, Task, TaskCreate

XP_PER_TASK = 25
XP_PER_LEVEL = 100

# (min_level, max_level, avatar_emoji, stage_name)
_EVOLUTION: list[tuple[int, int, str, str]] = [
    (1,  2,  "🥚", "Egg"),
    (3,  4,  "🐣", "Hatchling"),
    (5,  9,  "🐱", "Kitten"),
    (10, 19, "🐯", "Tiger"),
    (20, 999, "🐉", "Dragon"),
]


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


def _evolution_for_level(level: int) -> tuple[str, str]:
    for min_lv, max_lv, avatar, stage in _EVOLUTION:
        if min_lv <= level <= max_lv:
            return avatar, stage
    return "🐉", "Dragon"


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


def _day_count(conn: sqlite3.Connection, start: datetime, end: datetime) -> int:
    return conn.execute(
        "SELECT COUNT(*) FROM tasks "
        "WHERE completed = 1 AND completed_at >= ? AND completed_at < ?",
        (start.isoformat(), end.isoformat()),
    ).fetchone()[0]


# ---------------------------------------------------------------------------
# Pet
# ---------------------------------------------------------------------------

def get_pet(conn: sqlite3.Connection) -> Pet:
    row = conn.execute("SELECT name, xp FROM pet WHERE id = 1").fetchone()
    xp = row["xp"]
    level = _compute_level(xp)
    avatar, stage = _evolution_for_level(level)
    return Pet(
        name=row["name"],
        level=level,
        xp=xp,
        mood=_compute_mood(conn),
        xp_to_next_level=_xp_to_next_level(xp),
        evolution_stage=stage,
        avatar=avatar,
    )


def _award_xp(conn: sqlite3.Connection, amount: int) -> Pet:
    conn.execute("UPDATE pet SET xp = xp + ? WHERE id = 1", (amount,))
    conn.commit()
    return get_pet(conn)


# ---------------------------------------------------------------------------
# Stats
# ---------------------------------------------------------------------------

def get_stats(conn: sqlite3.Connection) -> Stats:
    now = datetime.now(timezone.utc)
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    week_ago = today_start - timedelta(days=7)

    total = conn.execute("SELECT COUNT(*) FROM tasks").fetchone()[0]
    completed_total = conn.execute(
        "SELECT COUNT(*) FROM tasks WHERE completed = 1"
    ).fetchone()[0]

    today_count = _day_count(conn, today_start, today_start + timedelta(days=1))

    week_count = conn.execute(
        "SELECT COUNT(*) FROM tasks WHERE completed = 1 AND completed_at >= ?",
        (week_ago.isoformat(),),
    ).fetchone()[0]

    # Streak: consecutive days with at least one completion.
    # If nothing done today yet, we start counting from yesterday.
    streak = 0
    offset = 0 if today_count > 0 else 1
    for i in range(offset, 31):
        day_s = today_start - timedelta(days=i)
        if _day_count(conn, day_s, day_s + timedelta(days=1)) > 0:
            streak += 1
        else:
            break

    return Stats(
        total_tasks=total,
        completed_tasks=completed_total,
        pending_tasks=total - completed_total,
        completed_today=today_count,
        completed_this_week=week_count,
        streak_days=streak,
        avg_per_day_last_7=round(week_count / 7, 1),
    )


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
