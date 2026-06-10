import sqlite3

import pytest
from fastapi.testclient import TestClient

from studypet.database import XP_PER_TASK, init_db
from studypet.server import app, get_conn


@pytest.fixture
def client():
    """TestClient backed by a fresh in-memory SQLite DB per test."""
    conn = sqlite3.connect(":memory:", check_same_thread=False)
    conn.row_factory = sqlite3.Row
    init_db(conn)

    def override_get_conn():
        yield conn

    app.dependency_overrides[get_conn] = override_get_conn
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()
    conn.close()


# ---------------------------------------------------------------------------
# GET /pet
# ---------------------------------------------------------------------------

def test_get_pet(client):
    r = client.get("/pet")
    assert r.status_code == 200
    body = r.json()
    assert body["name"] == "Pixel"
    assert body["level"] == 1
    assert body["xp"] == 0
    assert body["mood"] == "sad"
    assert "xp_to_next_level" in body


# ---------------------------------------------------------------------------
# POST /tasks
# ---------------------------------------------------------------------------

def test_create_task(client):
    r = client.post("/tasks", json={"title": "Study chapter 3"})
    assert r.status_code == 201
    body = r.json()
    assert body["id"] is not None
    assert body["title"] == "Study chapter 3"
    assert body["completed"] is False
    assert body["completed_at"] is None


def test_create_task_with_description(client):
    r = client.post("/tasks", json={"title": "Lab report", "description": "Due Friday"})
    assert r.status_code == 201
    assert r.json()["description"] == "Due Friday"


def test_create_task_missing_title(client):
    r = client.post("/tasks", json={})
    assert r.status_code == 422


# ---------------------------------------------------------------------------
# GET /tasks
# ---------------------------------------------------------------------------

def test_list_tasks_empty(client):
    r = client.get("/tasks")
    assert r.status_code == 200
    assert r.json() == []


def test_list_tasks(client):
    client.post("/tasks", json={"title": "Task A"})
    client.post("/tasks", json={"title": "Task B"})
    r = client.get("/tasks")
    assert r.status_code == 200
    assert len(r.json()) == 2


def test_list_tasks_filter_completed_true(client):
    r1 = client.post("/tasks", json={"title": "Done"}).json()
    client.post("/tasks", json={"title": "Pending"})
    client.put(f"/tasks/{r1['id']}/complete")

    r = client.get("/tasks", params={"completed": "true"})
    assert r.status_code == 200
    items = r.json()
    assert len(items) == 1
    assert items[0]["completed"] is True


def test_list_tasks_filter_completed_false(client):
    r1 = client.post("/tasks", json={"title": "Done"}).json()
    client.post("/tasks", json={"title": "Pending"})
    client.put(f"/tasks/{r1['id']}/complete")

    r = client.get("/tasks", params={"completed": "false"})
    assert r.status_code == 200
    items = r.json()
    assert len(items) == 1
    assert items[0]["completed"] is False


# ---------------------------------------------------------------------------
# PUT /tasks/{id}/complete
# ---------------------------------------------------------------------------

def test_complete_task(client):
    task_id = client.post("/tasks", json={"title": "Finish homework"}).json()["id"]
    r = client.put(f"/tasks/{task_id}/complete")
    assert r.status_code == 200
    body = r.json()
    assert body["task"]["completed"] is True
    assert body["task"]["completed_at"] is not None
    assert body["pet"]["xp"] == XP_PER_TASK
    assert body["xp_earned"] == XP_PER_TASK


def test_complete_task_updates_pet_mood(client):
    for i in range(3):
        tid = client.post("/tasks", json={"title": f"Task {i}"}).json()["id"]
        client.put(f"/tasks/{tid}/complete")
    pet = client.get("/pet").json()
    assert pet["mood"] in ("okay", "happy", "ecstatic")


def test_complete_task_already_done(client):
    task_id = client.post("/tasks", json={"title": "Once only"}).json()["id"]
    client.put(f"/tasks/{task_id}/complete")
    r = client.put(f"/tasks/{task_id}/complete")
    assert r.status_code == 400
    assert "already completed" in r.json()["detail"]


def test_complete_task_not_found(client):
    r = client.put("/tasks/9999/complete")
    assert r.status_code == 404
    assert "not found" in r.json()["detail"]


# ---------------------------------------------------------------------------
# DELETE /tasks/{id}
# ---------------------------------------------------------------------------

def test_delete_task(client):
    task_id = client.post("/tasks", json={"title": "Remove me"}).json()["id"]
    r = client.delete(f"/tasks/{task_id}")
    assert r.status_code == 204
    assert client.get("/tasks").json() == []


def test_delete_task_not_found(client):
    r = client.delete("/tasks/9999")
    assert r.status_code == 404
    assert "not found" in r.json()["detail"]


# ---------------------------------------------------------------------------
# GET /stats
# ---------------------------------------------------------------------------

def test_get_stats_empty(client):
    r = client.get("/stats")
    assert r.status_code == 200
    body = r.json()
    assert body["total_tasks"] == 0
    assert body["completed_tasks"] == 0
    assert body["pending_tasks"] == 0
    assert body["completed_today"] == 0
    assert body["streak_days"] == 0


def test_get_stats_after_completion(client):
    task_id = client.post("/tasks", json={"title": "Stat test"}).json()["id"]
    client.put(f"/tasks/{task_id}/complete")
    r = client.get("/stats")
    assert r.status_code == 200
    body = r.json()
    assert body["completed_tasks"] == 1
    assert body["completed_today"] == 1
    assert body["streak_days"] == 1


def test_get_pet_has_evolution(client):
    body = client.get("/pet").json()
    assert "evolution_stage" in body
    assert "avatar" in body
    assert body["evolution_stage"] == "Egg"
    assert body["avatar"] == "🥚"
