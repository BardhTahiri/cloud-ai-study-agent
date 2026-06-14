from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field

from backend.app.models.entities import TaskStatus


class CourseCreate(BaseModel):
    name: str = Field(..., min_length=2, max_length=120)
    description: str = Field(default="", max_length=500)


class CourseResponse(BaseModel):
    id: str
    name: str
    description: str
    created_at: datetime


class StudyTaskCreate(BaseModel):
    title: str = Field(..., min_length=2, max_length=160)
    course_id: str | None = None
    prompt: str = Field(default="", max_length=1000)
    material_text: str = Field(..., min_length=30)
    source_type: Literal["prompt", "text", "pdf"] = "text"
    source_name: str | None = None


class StudyTaskResponse(BaseModel):
    id: str
    title: str
    course_id: str | None
    prompt: str
    source_type: str
    source_name: str | None
    status: TaskStatus
    progress: int
    result: dict[str, Any] | None
    error: str | None
    created_at: datetime
    updated_at: datetime


class HealthResponse(BaseModel):
    status: str
    service: str
