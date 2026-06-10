# API Reference — StudyPet

Base URL: `http://localhost:8000`

All requests and responses use `application/json`.

---

## Pet

### GET /pet

Returns the current pet status.

**Response 200**
```json
{
  "name": "Pixel",
  "level": 2,
  "xp": 150,
  "mood": "happy",
  "xp_to_next_level": 50
}
```

---

## Tasks

### POST /tasks

Create a new task.

**Request body**
```json
{
  "title": "Finish lab report",
  "description": "Due Friday"
}
```
`description` is optional.

**Response 201**
```json
{
  "id": 1,
  "title": "Finish lab report",
  "description": "Due Friday",
  "completed": false,
  "completed_at": null,
  "created_at": "2026-06-09T10:00:00"
}
```

---

### GET /tasks

List all tasks.

**Query parameters**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `completed` | bool | (none) | Filter by completion status |

**Response 200**
```json
[
  {
    "id": 1,
    "title": "Finish lab report",
    "description": "Due Friday",
    "completed": false,
    "completed_at": null,
    "created_at": "2026-06-09T10:00:00"
  }
]
```

---

### PUT /tasks/{id}/complete

Mark a task as complete and award 25 XP to the pet.
Returns an error if the task is already completed.

**Response 200**
```json
{
  "task": {
    "id": 1,
    "title": "Finish lab report",
    "completed": true,
    "completed_at": "2026-06-09T11:00:00",
    "created_at": "2026-06-09T10:00:00"
  },
  "pet": {
    "name": "Pixel",
    "level": 1,
    "xp": 25,
    "mood": "okay",
    "xp_to_next_level": 75
  },
  "xp_earned": 25
}
```

**Response 400** — task already completed
```json
{ "detail": "Task is already completed" }
```

**Response 404** — task not found
```json
{ "detail": "Task not found" }
```

---

### DELETE /tasks/{id}

Delete a task by ID.

**Response 204** — no body

**Response 404**
```json
{ "detail": "Task not found" }
```
