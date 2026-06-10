# Testing Plan — StudyPet

## Strategy

Tests are written alongside each component — not at the end.
No test is ever deleted to make the suite pass; the code is fixed instead.

## Test Files

| File | Phase | What it covers |
|------|-------|----------------|
| `tests/test_database.py` | 4 | Database layer: CRUD, XP logic, mood calculation |
| `tests/test_server.py` | 6 | API endpoints via FastAPI `TestClient` |

## Database Tests (`test_database.py`)

| Test | Description |
|------|-------------|
| `test_create_task` | Creates a task and reads it back |
| `test_list_tasks_empty` | Returns empty list on fresh DB |
| `test_list_tasks` | Returns all inserted tasks |
| `test_complete_task` | Marks task complete, awards XP |
| `test_complete_task_already_done` | Raises error on double-complete |
| `test_delete_task` | Removes task from DB |
| `test_delete_task_not_found` | Raises error for missing ID |
| `test_pet_initial_state` | Pet starts at level 1, 0 XP |
| `test_pet_level_up` | Pet levels up at 100 XP |
| `test_pet_mood_sad` | 0 tasks today → sad |
| `test_pet_mood_okay` | 1–2 tasks today → okay |
| `test_pet_mood_happy` | 3–4 tasks today → happy |
| `test_pet_mood_ecstatic` | 5+ tasks today → ecstatic |

## API Tests (`test_server.py`)

| Test | Description |
|------|-------------|
| `test_get_pet` | GET /pet returns pet object |
| `test_create_task` | POST /tasks creates and returns task |
| `test_list_tasks` | GET /tasks returns list |
| `test_list_tasks_filter_completed` | GET /tasks?completed=true filters correctly |
| `test_complete_task` | PUT /tasks/{id}/complete awards XP |
| `test_complete_task_already_done` | Returns 400 on double-complete |
| `test_complete_task_not_found` | Returns 404 for unknown ID |
| `test_delete_task` | DELETE /tasks/{id} returns 204 |
| `test_delete_task_not_found` | Returns 404 for unknown ID |

## Running Tests

```bash
uv run pytest                          # all tests
uv run pytest -v                       # verbose output
uv run pytest tests/test_database.py  # database layer only
uv run pytest tests/test_server.py    # API layer only
uv run pytest --tb=short              # compact tracebacks
```

## Fixtures

- Database tests use an **in-memory SQLite** database created fresh per test.
- API tests use FastAPI's **`TestClient`** with the same in-memory DB injected
  via dependency override — no running server required.
