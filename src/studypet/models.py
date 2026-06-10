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
    evolution_stage: str
    avatar: str


class CompleteTaskResponse(BaseModel):
    task: Task
    pet: Pet
    xp_earned: int


class Stats(BaseModel):
    total_tasks: int
    completed_tasks: int
    pending_tasks: int
    completed_today: int
    completed_this_week: int
    streak_days: int
    avg_per_day_last_7: float
