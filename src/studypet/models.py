from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class TaskCreate(BaseModel):
    title: str
    description: Optional[str] = None


class Task(BaseModel):
    id: int
    title: str
    description: Optional[str] = None
    completed: bool
    completed_at: Optional[datetime] = None
    created_at: datetime


class Pet(BaseModel):
    name: str
    level: int
    xp: int
    mood: str
    xp_to_next_level: int


class CompleteTaskResponse(BaseModel):
    task: Task
    pet: Pet
    xp_earned: int
