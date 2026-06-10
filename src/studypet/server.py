import os
import sqlite3
from typing import Generator, Optional

import uvicorn
from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from studypet.database import (
    XP_PER_TASK,
    complete_task as db_complete_task,
    create_task as db_create_task,
    delete_task as db_delete_task,
    get_db_path,
    get_pet as db_get_pet,
    get_stats as db_get_stats,
    init_db,
    list_tasks as db_list_tasks,
)
from studypet.models import CompleteTaskResponse, Pet, Stats, Task, TaskCreate

app = FastAPI(title="StudyPet API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------------------------------------------------------------------------
# Dependency
# ---------------------------------------------------------------------------

def get_conn() -> Generator[sqlite3.Connection, None, None]:
    conn = sqlite3.connect(get_db_path(), check_same_thread=False)
    conn.row_factory = sqlite3.Row
    init_db(conn)
    try:
        yield conn
    finally:
        conn.close()


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@app.get("/pet", response_model=Pet)
def get_pet(conn: sqlite3.Connection = Depends(get_conn)) -> Pet:
    return db_get_pet(conn)


@app.get("/stats", response_model=Stats)
def get_stats(conn: sqlite3.Connection = Depends(get_conn)) -> Stats:
    return db_get_stats(conn)


@app.post("/tasks", response_model=Task, status_code=201)
def create_task(
    task_in: TaskCreate,
    conn: sqlite3.Connection = Depends(get_conn),
) -> Task:
    return db_create_task(conn, task_in)


@app.get("/tasks", response_model=list[Task])
def list_tasks(
    completed: Optional[bool] = None,
    conn: sqlite3.Connection = Depends(get_conn),
) -> list[Task]:
    return db_list_tasks(conn, completed)


@app.put("/tasks/{task_id}/complete", response_model=CompleteTaskResponse)
def complete_task(
    task_id: int,
    conn: sqlite3.Connection = Depends(get_conn),
) -> CompleteTaskResponse:
    try:
        task, pet = db_complete_task(conn, task_id)
    except ValueError as exc:
        msg = str(exc)
        status = 404 if "not found" in msg else 400
        raise HTTPException(status_code=status, detail=msg)
    return CompleteTaskResponse(task=task, pet=pet, xp_earned=XP_PER_TASK)


@app.delete("/tasks/{task_id}", status_code=204)
def delete_task(
    task_id: int,
    conn: sqlite3.Connection = Depends(get_conn),
) -> None:
    try:
        db_delete_task(conn, task_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main() -> None:
    host = os.environ.get("STUDYPET_HOST", "127.0.0.1")
    port = int(os.environ.get("STUDYPET_PORT", "8000"))
    uvicorn.run("studypet.server:app", host=host, port=port, reload=False)


if __name__ == "__main__":
    main()
