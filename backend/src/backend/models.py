from __future__ import annotations

from datetime import date
from uuid import uuid4

from pydantic import BaseModel, Field, field_validator


class TaskInput(BaseModel):
    name: str = Field(min_length=1, max_length=160)
    description: str = ""
    assignee: str = Field(min_length=1, max_length=80)
    duration: int = Field(ge=1, le=365)
    predecessor_ids: list[str] = Field(default_factory=list)
    start_offset: int = Field(default=0, ge=0, le=365)

    @field_validator("name", "assignee")
    @classmethod
    def strip_required(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("must not be empty")
        return value


class TaskCreate(TaskInput):
    id: str = Field(default_factory=lambda: str(uuid4()))


class TaskUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=160)
    description: str | None = None
    assignee: str | None = Field(default=None, min_length=1, max_length=80)
    duration: int | None = Field(default=None, ge=1, le=365)
    predecessor_ids: list[str] | None = None
    start_offset: int | None = Field(default=None, ge=0, le=365)


class Task(TaskInput):
    id: str
    start_date: date
    end_date: date


class Project(BaseModel):
    id: str = "planpilot-demo"
    name: str = "Biotech launch plan"
    start_date: date
    tasks: list[Task]
    revision: int = 1


class ProjectSnapshot(BaseModel):
    name: str
    start_date: date
    tasks: list[TaskCreate]


class ChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=1000)


class Change(BaseModel):
    task_id: str
    task_name: str
    description: str


class ChatResponse(BaseModel):
    reply: str
    changes: list[Change]
    project: Project
    can_undo: bool
