from __future__ import annotations

from datetime import date
from enum import StrEnum
from typing import Literal
from uuid import uuid4

from pydantic import BaseModel, Field, field_validator


class Person(StrEnum):
    ELENA = "Elena"
    MIKHAIL = "Mikhail"
    DARIA = "Daria"
    ANNA = "Anna"
    PAVEL = "Pavel"


class TaskInput(BaseModel):
    name: str = Field(min_length=1, max_length=160)
    description: str = ""
    assignees: list[Person] = Field(min_length=1)
    duration: int = Field(ge=1, le=365)
    predecessor_ids: list[str] = Field(default_factory=list)
    start_offset: int = Field(default=0, ge=0, le=365)

    @field_validator("name")
    @classmethod
    def strip_required(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("must not be empty")
        return value

    @field_validator("assignees")
    @classmethod
    def unique_assignees(cls, value: list[Person]) -> list[Person]:
        return list(dict.fromkeys(value))


class TaskCreate(TaskInput):
    id: str = Field(default_factory=lambda: str(uuid4()))


class TaskUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=160)
    description: str | None = None
    assignees: list[Person] | None = Field(default=None, min_length=1)
    duration: int | None = Field(default=None, ge=1, le=365)
    predecessor_ids: list[str] | None = None
    start_offset: int | None = Field(default=None, ge=0, le=365)

    @field_validator("assignees")
    @classmethod
    def unique_assignees(cls, value: list[Person] | None) -> list[Person] | None:
        return list(dict.fromkeys(value)) if value is not None else None


class Task(TaskInput):
    id: str
    start_date: date
    end_date: date
    man_hours: int


class Project(BaseModel):
    id: str = "biocad-demo"
    name: str = "Biotech launch plan"
    start_date: date
    tasks: list[Task]
    team: list[Person] = Field(default_factory=lambda: list(Person))
    revision: int = 1


class ProjectSnapshot(BaseModel):
    name: str
    start_date: date
    tasks: list[TaskCreate]


class ChatMessage(BaseModel):
    role: Literal["user", "assistant"]
    content: str = Field(min_length=1, max_length=4000)


class ChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=1000)
    history: list[ChatMessage] = Field(default_factory=list, max_length=20)


class Change(BaseModel):
    task_id: str
    task_name: str
    description: str


class AgentUsage(BaseModel):
    model: str
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0
    cost_usd: float = 0


class ChatResponse(BaseModel):
    reply: str
    changes: list[Change]
    project: Project
    can_undo: bool
    usage: AgentUsage
