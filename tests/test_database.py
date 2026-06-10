import sqlite3
from datetime import datetime, timedelta, timezone

import pytest

from studypet.database import (
    XP_PER_LEVEL,
    XP_PER_TASK,
    complete_task,
    create_task,
    delete_task,
    get_pet,
    get_stats,
    get_task,
    init_db,
    list_tasks,
)
from studypet.models import TaskCreate


@pytest.fixture
def conn():
    """Fresh in-memory SQLite connection, fully initialized, per test."""
    c = sqlite3.connect(":memory:", check_same_thread=False)
    c.row_factory = sqlite3.Row
    init_db(c)
    yield c
    c.close()


# ---------------------------------------------------------------------------
# Pet
# ---------------------------------------------------------------------------

def test_pet_initial_state(conn):
    pet = get_pet(conn)
    assert pet.name == "Pixel"
    assert pet.xp == 0
    assert pet.level == 1
    assert pet.xp_to_next_level == XP_PER_LEVEL
    assert pet.mood == "sad"


def test_pet_level_up(conn):
    # Complete enough tasks to exceed level boundary
    tasks_needed = XP_PER_LEVEL // XP_PER_TASK  # 100 / 25 = 4
    for i in range(tasks_needed):
        t = create_task(conn, TaskCreate(title=f"Task {i}"))
        complete_task(conn, t.id)
    pet = get_pet(conn)
    assert pet.level == 2
    assert pet.xp == XP_PER_LEVEL
    assert pet.xp_to_next_level == XP_PER_LEVEL


def test_pet_mood_sad(conn):
    pet = get_pet(conn)
    assert pet.mood == "sad"


def test_pet_mood_okay(conn):
    for i in range(2):
        t = create_task(conn, TaskCreate(title=f"Task {i}"))
        complete_task(conn, t.id)
    assert get_pet(conn).mood == "okay"


def test_pet_mood_happy(conn):
    for i in range(4):
        t = create_task(conn, TaskCreate(title=f"Task {i}"))
        complete_task(conn, t.id)
    assert get_pet(conn).mood == "happy"


def test_pet_mood_ecstatic(conn):
    for i in range(5):
        t = create_task(conn, TaskCreate(title=f"Task {i}"))
        complete_task(conn, t.id)
    assert get_pet(conn).mood == "ecstatic"


# ---------------------------------------------------------------------------
# Tasks — create / read
# ---------------------------------------------------------------------------

def test_create_task(conn):
    task = create_task(conn, TaskCreate(title="Study Python", description="Chapter 7"))
    assert task.id is not None
    assert task.title == "Study Python"
    assert task.description == "Chapter 7"
    assert task.completed is False
    assert task.completed_at is None
    assert isinstance(task.created_at, datetime)


def test_create_task_no_description(conn):
    task = create_task(conn, TaskCreate(title="Quick task"))
    assert task.description is None


def test_get_task_returns_task(conn):
    created = create_task(conn, TaskCreate(title="Find me"))
    fetched = get_task(conn, created.id)
    assert fetched is not None
    assert fetched.id == created.id
    assert fetched.title == "Find me"


def test_get_task_missing_returns_none(conn):
    assert get_task(conn, 9999) is None


# ---------------------------------------------------------------------------
# Tasks — list
# ---------------------------------------------------------------------------

def test_list_tasks_empty(conn):
    assert list_tasks(conn) == []


def test_list_tasks_returns_all(conn):
    create_task(conn, TaskCreate(title="A"))
    create_task(conn, TaskCreate(title="B"))
    tasks = list_tasks(conn)
    assert len(tasks) == 2


def test_list_tasks_filter_completed(conn):
    t1 = create_task(conn, TaskCreate(title="Done"))
    t2 = create_task(conn, TaskCreate(title="Pending"))
    complete_task(conn, t1.id)

    done = list_tasks(conn, completed=True)
    pending = list_tasks(conn, completed=False)

    assert len(done) == 1
    assert done[0].id == t1.id
    assert len(pending) == 1
    assert pending[0].id == t2.id


# ---------------------------------------------------------------------------
# Tasks — complete
# ---------------------------------------------------------------------------

def test_complete_task(conn):
    t = create_task(conn, TaskCreate(title="Finish report"))
    task, pet = complete_task(conn, t.id)

    assert task.completed is True
    assert task.completed_at is not None
    assert pet.xp == XP_PER_TASK


def test_complete_task_awards_xp(conn):
    before = get_pet(conn).xp
    t = create_task(conn, TaskCreate(title="Earn XP"))
    complete_task(conn, t.id)
    after = get_pet(conn).xp
    assert after == before + XP_PER_TASK


def test_complete_task_already_done(conn):
    t = create_task(conn, TaskCreate(title="Once only"))
    complete_task(conn, t.id)
    with pytest.raises(ValueError, match="already completed"):
        complete_task(conn, t.id)


def test_complete_task_not_found(conn):
    with pytest.raises(ValueError, match="not found"):
        complete_task(conn, 9999)


# ---------------------------------------------------------------------------
# Tasks — delete
# ---------------------------------------------------------------------------

def test_delete_task(conn):
    t = create_task(conn, TaskCreate(title="Remove me"))
    delete_task(conn, t.id)
    assert get_task(conn, t.id) is None
    assert list_tasks(conn) == []


def test_delete_task_not_found(conn):
    with pytest.raises(ValueError, match="not found"):
        delete_task(conn, 9999)


# ---------------------------------------------------------------------------
# Evolution
# ---------------------------------------------------------------------------

def test_pet_evolution_egg(conn):
    pet = get_pet(conn)
    assert pet.evolution_stage == "Egg"
    assert pet.avatar == "🥚"


def test_pet_evolution_hatchling(conn):
    # Level 3 requires 200 XP = 8 completed tasks
    for i in range(8):
        t = create_task(conn, TaskCreate(title=f"T{i}"))
        complete_task(conn, t.id)
    pet = get_pet(conn)
    assert pet.level == 3
    assert pet.evolution_stage == "Hatchling"
    assert pet.avatar == "🐣"


def test_pet_evolution_kitten(conn):
    # Level 5 requires 400 XP = 16 completed tasks
    for i in range(16):
        t = create_task(conn, TaskCreate(title=f"T{i}"))
        complete_task(conn, t.id)
    pet = get_pet(conn)
    assert pet.level == 5
    assert pet.evolution_stage == "Kitten"
    assert pet.avatar == "🐱"


# ---------------------------------------------------------------------------
# Stats
# ---------------------------------------------------------------------------

def test_get_stats_empty(conn):
    s = get_stats(conn)
    assert s.total_tasks == 0
    assert s.completed_tasks == 0
    assert s.pending_tasks == 0
    assert s.completed_today == 0
    assert s.completed_this_week == 0
    assert s.streak_days == 0
    assert s.avg_per_day_last_7 == 0.0


def test_get_stats_counts(conn):
    t1 = create_task(conn, TaskCreate(title="A"))
    t2 = create_task(conn, TaskCreate(title="B"))
    create_task(conn, TaskCreate(title="C"))
    complete_task(conn, t1.id)
    complete_task(conn, t2.id)
    s = get_stats(conn)
    assert s.total_tasks == 3
    assert s.completed_tasks == 2
    assert s.pending_tasks == 1
    assert s.completed_today == 2


def test_get_stats_streak(conn):
    t = create_task(conn, TaskCreate(title="Today"))
    complete_task(conn, t.id)
    s = get_stats(conn)
    assert s.streak_days == 1


def test_get_stats_avg(conn):
    for i in range(7):
        t = create_task(conn, TaskCreate(title=f"T{i}"))
        complete_task(conn, t.id)
    s = get_stats(conn)
    assert s.avg_per_day_last_7 == 1.0
