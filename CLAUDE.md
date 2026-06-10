# CLAUDE.md — StudyPet

## Project Overview

StudyPet is a virtual pet productivity tracker built as a CS final project.
Users complete tasks to earn XP, level up their pet, and see mood changes
based on daily productivity.

## Stack

- **Language:** Python 3.11 via `uv`
- **Server:** FastAPI + Uvicorn, SQLite (via stdlib `sqlite3`)
- **Models:** Pydantic v2
- **CLI client:** Click + httpx
- **TUI client:** Textual + httpx
- **Web client:** Vanilla HTML/CSS/JS
- **Tests:** pytest + pytest-anyio

## Key Rules

1. All clients (CLI, TUI, web) **must** call the REST API — never SQLite directly.
2. The SQLite database file is `studypet.db` in the project root (git-ignored).
3. Default server URL is `http://localhost:8000`. Clients read `STUDYPET_URL`
   env var to override.
4. Do not delete tests to make them pass — fix the code instead.

## Common Commands

```bash
uv sync                        # install / refresh deps
uv run studypet-server         # start API server
uv run studypet-cli --help     # CLI help
uv run studypet-tui            # launch TUI
uv run pytest                  # run all tests
uv run pytest -v               # verbose
```

## File Layout

```
src/studypet/
  __init__.py
  models.py      # Pydantic models: Task, Pet, TaskCreate, etc.
  database.py    # All SQLite logic lives here
  server.py      # FastAPI app with all route handlers
cli/
  cli.py         # Click CLI — HTTP only
tui/
  tui.py         # Textual TUI — HTTP only
web/
  index.html / style.css / app.js
tests/
  test_database.py
  test_server.py
docs/
  requirements.md
  architecture.md
  api.md
  testing-plan.md
  architecture.mmd
```

## Environment Variables

| Variable | Default | Purpose |
|----------|---------|---------|
| `STUDYPET_URL` | `http://localhost:8000` | API base URL for clients |
| `STUDYPET_DB` | `studypet.db` | Path to SQLite database file |
