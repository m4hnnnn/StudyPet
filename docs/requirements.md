# Requirements — StudyPet

## Functional Requirements

### Tasks
- FR-01: Users can create a task with a title and optional description.
- FR-02: Users can list all tasks (pending and completed).
- FR-03: Users can mark a task as complete; doing so awards XP to the pet.
- FR-04: Users can delete a task.

### Pet
- FR-05: There is exactly one pet per database instance.
- FR-06: The pet has a name, level, total XP, and a mood.
- FR-07: Completing a task awards 25 XP.
- FR-08: The pet levels up every 100 XP (level = XP // 100 + 1).
- FR-09: Mood is computed dynamically from tasks completed in the last 24 hours:
  - 0 completed → "sad"
  - 1–2 completed → "okay"
  - 3–4 completed → "happy"
  - 5+ completed → "ecstatic"

### Clients
- FR-10: A REST API server exposes all functionality over HTTP/JSON.
- FR-11: A CLI client interacts with the server via HTTP (not SQLite).
- FR-12: A TUI client interacts with the server via HTTP (not SQLite).
- FR-13: A web client interacts with the server via HTTP (not SQLite).

## Non-Functional Requirements

- NFR-01: Server starts in under 3 seconds on a standard laptop.
- NFR-02: All API responses return in under 500 ms for typical payloads.
- NFR-03: The database file is excluded from version control.
- NFR-04: All dependencies are declared in `pyproject.toml` and managed by `uv`.
- NFR-05: The test suite must pass without modifying or deleting any test.

## Out of Scope

- Multi-user support (single pet per instance only).
- Authentication / authorization.
- Task priorities or due dates (v1).
- Persistent pet names set by user (name is fixed at "Pixel" in v1).
